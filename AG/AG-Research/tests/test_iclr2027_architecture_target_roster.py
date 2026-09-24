from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest
from dataclasses import fields
from typing import Any, get_type_hints
from unittest.mock import patch

import build_iclr2027_architecture_target_roster as roster_builder
import run_exp08_architecture as architecture_runner
from iclr2027.architecture_target_roster import (
    AdmissionBindingV1,
    BlindOverlapCheckV1,
    FreezeReceiptV2,
    GeometryReceiptV1,
    IndependentReviewV1,
    LegacyBindingsV1,
    SiteLocatorV1,
    SourceCaptureV1,
    TargetSpecV1,
    TargetRosterError,
    canonical_sha256,
    verify_admission_inputs,
    verify_blind_overlap_check,
    verify_frozen_target_roster,
    verify_geometry_receipt_set,
    verify_site_locator_set,
    verify_source_capture_set,
    verify_target_spec_set,
    verify_target_roster,
)
from iclr2027 import precall_design_lock as precall_design_lock
from iclr2027.precall_design_lock import (
    NeedsContextError,
    require_authenticated_pre_call_authority,
)
from build_iclr2027_architecture_target_roster import build_frozen_roster
from iclr2027.dataset import (
    PROGRAM_ORDER,
    registry_expected_bundle_counts,
    verified_development_target_count,
)
from iclr2027.run_manifest import run_manifest_identity, validate_run_manifest


def digest(value: object) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def reseal(roster: dict[str, object], field: str) -> dict[str, object]:
    payload = {key: value for key, value in roster.items() if key != field}
    roster[field] = hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    return roster


def make_roster(
    allocation: tuple[int, int, int] = (12, 11, 11),
    extra_target_field: dict[str, object] | None = None,
) -> dict[str, object]:
    sites = []
    targets = []
    for site_index, count in enumerate(allocation):
        site_ref = f"site-{site_index:02d}"
        sites.append(
            {
                "site_ref": site_ref,
                "area_bin": f"area-bin-{site_index:02d}",
            }
        )
        for target_index in range(count):
            target_ordinal = len(targets)
            target = {
                "target_ref": f"{site_ref}-target-{target_index:02d}",
                "site_ref": site_ref,
                "program": "architecture",
                "subject_kind": "built_form",
                "attempt_stage": "attempt-01",
                "route_kind": "route-a",
                "target_spec_sha256": digest(f"target:{site_ref}:{target_index:02d}"),
                "source_ids": (
                    f"source-{target_ordinal * 2:04d}",
                    f"source-{target_ordinal * 2 + 1:04d}",
                ),
            }
            if extra_target_field:
                target.update(extra_target_field)
            targets.append(target)
    roster: dict[str, object] = {
        "schema_version": "ace.iclr2027.architecture_target_roster.v1",
        "roster_version": "v1",
        "projection_identity_commitment": digest("projection"),
        "split": "dev",
        "site_count": 3,
        "target_count": 34,
        "allocation": allocation,
        "sites": tuple(sites),
        "targets": tuple(targets),
        "roster_sha256": "",
    }
    return reseal(roster, "roster_sha256")


def protected_public_mutations() -> tuple[tuple[str, object], ...]:
    return (
        ("pnu", "1234567890123456789"),
        ("address", "not-public"),
        ("uri", "https://example.invalid/private"),
        ("file_path", "C:\\private\\evidence.json"),
        ("condition", "opaque-condition"),
        ("expected_outcome", "approve"),
        ("mutation", "altered"),
        ("gold", "answer"),
        ("private", "answer"),
        ("internal", "answer"),
        ("secret", "answer"),
        ("native", "answer"),
        ("challenged", "answer"),
        ("notes", {"nested": {"address": "not-public"}}),
        ("notes", {"nested": "https://example.invalid/private"}),
        ("notes", {"nested": "C:\\private\\evidence.json"}),
        ("notes", {"nested": "1234567890123456789"}),
    )


def set_digest(rows: list[dict[str, object]]) -> str:
    """Hand-built canonical set digest for admission fixtures."""
    return hashlib.sha256(
        json.dumps(
            sorted(
                rows,
                key=lambda row: json.dumps(row, sort_keys=True, separators=(",", ":")),
            ),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def oracle_record_sha256(value: dict[str, object], self_hash_field: str) -> str:
    """Independent test-owned canonical record digest."""
    payload = {key: item for key, item in value.items() if key != self_hash_field}
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def make_admission_inputs() -> dict[str, object]:
    roster = make_roster()
    captures: list[dict[str, object]] = []
    target_specs: list[dict[str, object]] = []
    receipts: list[dict[str, object]] = []
    raw_bytes_by_source_id: dict[str, bytes] = {}
    mutable_targets = list(copy.deepcopy(roster["targets"]))
    families = ("geometry", "law", "parking", "program", "site")

    for target in mutable_targets:
        target_ref = target["target_ref"]
        source_ids: list[str] = []
        evidence_family_sources: dict[str, tuple[str, ...]] = {}
        for family_index, family in enumerate(families):
            source_id = f"source-{len(captures):04d}"
            raw = f"capture:{source_id}".encode("utf-8")
            raw_bytes_by_source_id[source_id] = raw
            source_ids.append(source_id)
            declared_families = tuple(sorted((family, families[family_index - 1])))
            captures.append(
                {
                    "schema_version": "ace.iclr2027.architecture_source_capture.v1",
                    "source_id": source_id,
                    "publisher": "fixture-publisher",
                    "canonical_uri": f"https://example.invalid/{source_id}",
                    "retrieved_at": "2026-08-31T00:00:00Z",
                    "effective_at": "2026-08-31T00:00:00Z",
                    "media_type": "application/json",
                    "byte_length": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "etag": "fixture-etag",
                    "last_modified": "2026-08-31T00:00:00Z",
                    "license": "fixture-license",
                    "redistribution_status": "restricted",
                    "evidence_families": declared_families,
                }
            )
        for family_index, family in enumerate(families):
            evidence_family_sources[family] = tuple(
                sorted(
                    (
                        source_ids[family_index],
                        source_ids[(family_index + 1) % len(families)],
                    )
                )
            )
        receipt = {
            "schema_version": "ace.iclr2027.architecture_geometry_receipt.v1",
            "target_ref": target_ref,
            "input_geometry_sha256": digest(f"input:{target_ref}"),
            "materializer_code_sha256": digest("materializer:v1"),
            "output_geometry_sha256": digest(f"output:{target_ref}"),
            "compile_log_sha256": digest(f"compile:{target_ref}"),
            "hard_pass": True,
            "receipt_sha256": "",
        }
        receipt["receipt_sha256"] = oracle_record_sha256(receipt, "receipt_sha256")
        receipts.append(receipt)
        spec = {
            "schema_version": "ace.iclr2027.architecture_target_spec.v1",
            "target_ref": target_ref,
            "normalized_subject_identity": f"normalized-subject-{len(target_specs):02d}",
            "evidence_family_sources": evidence_family_sources,
            "geometry_receipt_sha256": receipt["receipt_sha256"],
            "target_spec_sha256": "",
        }
        spec["target_spec_sha256"] = oracle_record_sha256(spec, "target_spec_sha256")
        target["target_spec_sha256"] = spec["target_spec_sha256"]
        target["source_ids"] = tuple(sorted(source_ids))
        target_specs.append(spec)

    roster["targets"] = tuple(mutable_targets)
    reseal(roster, "roster_sha256")
    locator_source_ids: list[str] = []
    for _ in range(3):
        locator_source_id = f"source-{len(captures):04d}"
        raw = f"capture:{locator_source_id}".encode("utf-8")
        raw_bytes_by_source_id[locator_source_id] = raw
        locator_source_ids.append(locator_source_id)
        captures.append(
            {
                "schema_version": "ace.iclr2027.architecture_source_capture.v1",
                "source_id": locator_source_id,
                "publisher": "fixture-publisher",
                "canonical_uri": f"https://example.invalid/{locator_source_id}",
                "retrieved_at": "2026-08-31T00:00:00Z",
                "effective_at": "2026-08-31T00:00:00Z",
                "media_type": "application/json",
                "byte_length": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "etag": "fixture-etag",
                "last_modified": "2026-08-31T00:00:00Z",
                "license": "fixture-license",
                "redistribution_status": "restricted",
                "evidence_families": ("site",),
            }
        )
    locators = []
    for index, site in enumerate(roster["sites"]):
        bound_source_ids = tuple(
            sorted(
                (
                    locator_source_ids[index],
                    locator_source_ids[(index + 1) % len(locator_source_ids)],
                )
            )
        )
        locators.append(
            {
                "schema_version": "ace.iclr2027.architecture_site_locator.v1",
                "internal_site_id": f"internal-site-{index:02d}",
                "pnu": f"12345678901234567{index:02d}",
                "split": "dev",
                "area_bin": site["area_bin"],
                "parcel_geometry_sha256": digest(f"parcel:{index}"),
                "project_cluster_id": f"cluster-{index:02d}",
                "source_capture_ids": bound_source_ids,
            }
        )
    locator_set_sha256 = set_digest(locators)
    protected_roster_commitment = digest("protected-roster")
    blind_check = {
        "schema_version": "ace.iclr2027.architecture_blind_overlap_check.v1",
        "locator_set_sha256": locator_set_sha256,
        "protected_roster_commitment": protected_roster_commitment,
        "overlap_found": False,
        "checked_site_count": 3,
        "audit_sha256": digest("blind-audit"),
        "record_sha256": "",
    }
    blind_check["record_sha256"] = oracle_record_sha256(blind_check, "record_sha256")
    return {
        "roster": roster,
        "target_specs": target_specs,
        "locators": locators,
        "source_captures": captures,
        "raw_bytes_by_source_id": raw_bytes_by_source_id,
        "geometry_receipts": receipts,
        "blind_check": blind_check,
        "protected_roster_commitment": protected_roster_commitment,
    }


def replace_shared_target_source_with_missing(inputs: dict[str, object]) -> None:
    spec = inputs["target_specs"][0]
    old_source = spec["evidence_family_sources"]["geometry"][0]
    missing_source = "missing-target-source"
    for family, source_ids in spec["evidence_family_sources"].items():
        if old_source in source_ids:
            spec["evidence_family_sources"][family] = tuple(
                sorted(
                    missing_source if item == old_source else item
                    for item in source_ids
                )
            )
    spec["target_spec_sha256"] = oracle_record_sha256(spec, "target_spec_sha256")
    target = inputs["roster"]["targets"][0]
    target["source_ids"] = tuple(
        sorted(
            missing_source if item == old_source else item
            for item in target["source_ids"]
        )
    )
    target["target_spec_sha256"] = spec["target_spec_sha256"]
    reseal(inputs["roster"], "roster_sha256")


def make_legacy_bindings() -> dict[str, object]:
    return {
        "schema_version": "ace.iclr2027.architecture_legacy_bindings.v1",
        "registry_version": "legacy-registry-v1",
        "registry_core_sha256": digest("legacy-registry-core"),
        "projection_identity_commitment": digest("projection"),
        "split_manifest_sha256": digest("legacy-split-manifest"),
        "public_registry_sha256": digest("legacy-public-registry"),
        "public_case_set_sha256": digest("legacy-public-case-set"),
        "existing_dev_site_count": 5,
        "existing_dev_target_count": 30,
    }


def write_complete_inputs(root: Path, *, corrupt_source: bool = False) -> Path:
    inputs = make_admission_inputs()
    root.mkdir()
    binding = verify_admission_inputs(**inputs)
    admission_hash = canonical_sha256(
        {field.name: getattr(binding, field.name) for field in fields(binding)}
    )
    review = {
        "schema_version": "ace.iclr2027.architecture_independent_review.v1",
        "reviewed_target_roster_sha256": binding.target_roster_sha256,
        "reviewed_admission_binding_sha256": admission_hash,
        "status": "approved",
        "reviewer_identity_commitment": digest("independent-reviewer"),
        "review_sha256": "",
    }
    review["review_sha256"] = canonical_sha256(
        review, omit=frozenset({"review_sha256"})
    )
    named_payloads = {
        "legacy_bindings.json": make_legacy_bindings(),
        "target_roster.json": inputs["roster"],
        "site_locators.json": inputs["locators"],
        "target_specs.json": inputs["target_specs"],
        "source_captures.json": inputs["source_captures"],
        "geometry_receipts.json": inputs["geometry_receipts"],
        "blind_overlap_check.json": inputs["blind_check"],
        "independent_review.json": review,
    }
    for name, payload in named_payloads.items():
        (root / name).write_text(
            json.dumps(
                payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
    source_objects = root / "source_objects"
    source_objects.mkdir()
    raw_bytes = inputs["raw_bytes_by_source_id"]
    captures = inputs["source_captures"]
    self_check = isinstance(raw_bytes, dict) and isinstance(captures, list)
    if not self_check:
        raise AssertionError("fixture_contract")
    for index, capture in enumerate(captures):
        source_id = capture["source_id"]
        sha256 = capture["sha256"]
        raw = raw_bytes[source_id]
        if corrupt_source and index == 0:
            raw = b"corrupt-source"
        (source_objects / f"{sha256}.bin").write_bytes(raw)
    return root


def build_runner_sidecar(root: Path) -> tuple[Path, Path]:
    """Build a reviewed sidecar bound to the repository's frozen projection."""

    root.mkdir()
    repository_root = Path(__file__).resolve().parents[1]
    legacy_root = repository_root / "data" / "iclr2027"
    legacy_receipt = json.loads(
        (legacy_root / "freeze_receipt.json").read_text(encoding="utf-8")
    )
    input_root = write_complete_inputs(root / "input")

    roster_path = input_root / "target_roster.json"
    roster = json.loads(roster_path.read_text(encoding="utf-8"))
    roster["projection_identity_commitment"] = legacy_receipt["identity_commitment"]
    roster["roster_sha256"] = canonical_sha256(
        roster, omit=frozenset({"roster_sha256"})
    )
    roster_path.write_text(
        json.dumps(roster, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    legacy_bindings = {
        "schema_version": "ace.iclr2027.architecture_legacy_bindings.v1",
        "registry_version": legacy_receipt["registry_version"],
        "registry_core_sha256": legacy_receipt["registry_core_sha256"],
        "projection_identity_commitment": legacy_receipt["identity_commitment"],
        "split_manifest_sha256": legacy_receipt["split_manifest_sha256"],
        "public_registry_sha256": legacy_receipt["public_registry_sha256"],
        "public_case_set_sha256": legacy_receipt["public_case_set_sha256"],
        "existing_dev_site_count": 5,
        "existing_dev_target_count": 30,
    }
    (input_root / "legacy_bindings.json").write_text(
        json.dumps(
            legacy_bindings,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    def read_input(name: str) -> object:
        return json.loads((input_root / name).read_text(encoding="utf-8"))

    captures = read_input("source_captures.json")
    if not isinstance(captures, list):
        raise AssertionError("source capture fixture is invalid")
    raw_bytes = {
        capture["source_id"]: (
            input_root / "source_objects" / f"{capture['sha256']}.bin"
        ).read_bytes()
        for capture in captures
    }
    binding = verify_admission_inputs(
        roster=roster,
        target_specs=read_input("target_specs.json"),
        locators=read_input("site_locators.json"),
        source_captures=captures,
        raw_bytes_by_source_id=raw_bytes,
        geometry_receipts=read_input("geometry_receipts.json"),
        blind_check=read_input("blind_overlap_check.json"),
        protected_roster_commitment=read_input("blind_overlap_check.json")[
            "protected_roster_commitment"
        ],
    )
    admission_hash = canonical_sha256(
        {field.name: getattr(binding, field.name) for field in fields(binding)}
    )
    review = read_input("independent_review.json")
    if not isinstance(review, dict):
        raise AssertionError("review fixture is invalid")
    review["reviewed_target_roster_sha256"] = binding.target_roster_sha256
    review["reviewed_admission_binding_sha256"] = admission_hash
    review["review_sha256"] = canonical_sha256(
        review, omit=frozenset({"review_sha256"})
    )
    (input_root / "independent_review.json").write_text(
        json.dumps(review, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    release_root = root / "release"
    build_frozen_roster(input_root, release_root)
    return (
        release_root / "public" / "architecture_target_roster.json",
        release_root / "public" / "architecture_freeze_receipt.v2.json",
    )


class TargetRosterSchemaTests(unittest.TestCase):
    def test_exact_12_11_11_roster_is_accepted(self) -> None:
        roster = make_roster(allocation=(12, 11, 11))
        parsed = verify_target_roster(roster)
        self.assertEqual((parsed.site_count, parsed.target_count), (3, 34))

    def test_evidence_fields_and_conditions_cannot_inflate_targets(self) -> None:
        roster = make_roster(allocation=(12, 11, 11))
        targets = roster["targets"]
        self.assertIsInstance(targets, tuple)
        mutable_targets = list(copy.deepcopy(targets))
        mutable_targets[1]["target_spec_sha256"] = mutable_targets[0][
            "target_spec_sha256"
        ]
        roster["targets"] = tuple(mutable_targets)
        with self.assertRaisesRegex(
            TargetRosterError, "target_spec_duplicate_or_mutated"
        ):
            verify_target_roster(reseal(roster, "roster_sha256"))

    def test_exact_public_rows_accept_source_ids_and_reject_legacy_fields(self) -> None:
        roster = make_roster()
        parsed = verify_target_roster(roster)
        self.assertEqual(parsed.sites[0]["area_bin"], "area-bin-00")
        self.assertEqual(
            parsed.targets[0]["source_ids"], ("source-0000", "source-0001")
        )
        targets = roster["targets"]
        self.assertIsInstance(targets, tuple)
        invalid_targets = list(copy.deepcopy(targets))
        invalid_targets[0]["evidence_families"] = ("geometry",)
        roster["targets"] = tuple(invalid_targets)
        with self.assertRaisesRegex(TargetRosterError, "target_keys"):
            verify_target_roster(reseal(roster, "roster_sha256"))

    def test_public_records_reject_protected_values_recursively(self) -> None:
        for key, value in protected_public_mutations():
            with self.subTest(key=key):
                with self.assertRaisesRegex(TargetRosterError, "protected_identifier"):
                    verify_target_roster(make_roster(extra_target_field={key: value}))


class TargetRosterAdmissionTests(unittest.TestCase):
    def test_valid_admission_returns_only_six_non_sensitive_hashes(self) -> None:
        binding = verify_admission_inputs(**make_admission_inputs())
        self.assertIsInstance(binding, AdmissionBindingV1)
        self.assertEqual(
            tuple(binding.__dataclass_fields__),
            (
                "target_roster_sha256",
                "locator_set_sha256",
                "source_capture_set_sha256",
                "target_spec_set_sha256",
                "geometry_receipt_set_sha256",
                "blind_overlap_check_sha256",
            ),
        )
        self.assertTrue(
            all(len(getattr(binding, field.name)) == 64 for field in fields(binding))
        )

    def test_every_target_has_all_five_bound_families(self) -> None:
        inputs = make_admission_inputs()
        del inputs["target_specs"][0]["evidence_family_sources"]["parking"]
        with self.assertRaisesRegex(
            TargetRosterError, "target_source_coverage_incomplete"
        ):
            verify_admission_inputs(**inputs)

    def test_blind_check_binds_exact_locator_and_protected_roster_commitments(
        self,
    ) -> None:
        inputs = make_admission_inputs()
        inputs["blind_check"]["locator_set_sha256"] = "0" * 64
        with self.assertRaisesRegex(TargetRosterError, "blinded_membership_check"):
            verify_admission_inputs(**inputs)

    def test_project_cluster_and_parcel_overlap_are_rejected(self) -> None:
        inputs = make_admission_inputs()
        inputs["locators"][1]["project_cluster_id"] = inputs["locators"][0][
            "project_cluster_id"
        ]
        with self.assertRaisesRegex(
            TargetRosterError, "site_or_project_cluster_overlap"
        ):
            verify_admission_inputs(**inputs)

    def test_private_schema_versions_are_exact(self) -> None:
        inputs = make_admission_inputs()
        captures = copy.deepcopy(inputs["source_captures"])
        captures[0]["schema_version"] = "ace.iclr2027.source_capture.v1"
        with self.assertRaisesRegex(TargetRosterError, "source_capture_schema"):
            SourceCaptureV1.from_dict(captures[0])
        locator = copy.deepcopy(inputs["locators"][0])
        locator["schema_version"] = "ace.iclr2027.site_locator.v1"
        with self.assertRaisesRegex(TargetRosterError, "site_locator_schema"):
            SiteLocatorV1.from_dict(locator)
        spec = copy.deepcopy(inputs["target_specs"][0])
        spec["schema_version"] = "ace.iclr2027.target_spec.v1"
        spec["target_spec_sha256"] = canonical_sha256(
            spec, omit=frozenset({"target_spec_sha256"})
        )
        with self.assertRaisesRegex(TargetRosterError, "target_spec_schema"):
            TargetSpecV1.from_dict(spec)
        receipt = copy.deepcopy(inputs["geometry_receipts"][0])
        receipt["schema_version"] = "ace.iclr2027.geometry_receipt.v1"
        receipt["receipt_sha256"] = canonical_sha256(
            receipt, omit=frozenset({"receipt_sha256"})
        )
        with self.assertRaisesRegex(TargetRosterError, "geometry_receipt_schema"):
            GeometryReceiptV1.from_dict(receipt)
        blind = copy.deepcopy(inputs["blind_check"])
        blind["schema_version"] = "ace.iclr2027.blind_overlap_check.v1"
        blind["record_sha256"] = canonical_sha256(
            blind, omit=frozenset({"record_sha256"})
        )
        with self.assertRaisesRegex(TargetRosterError, "blinded_membership_check"):
            BlindOverlapCheckV1.from_dict(blind)

    def test_train_locator_is_rejected_even_with_resealed_blind_record(self) -> None:
        inputs = make_admission_inputs()
        inputs["locators"][0]["split"] = "train"
        inputs["blind_check"]["locator_set_sha256"] = set_digest(inputs["locators"])
        inputs["blind_check"]["record_sha256"] = canonical_sha256(
            inputs["blind_check"], omit=frozenset({"record_sha256"})
        )
        with self.assertRaisesRegex(TargetRosterError, "locator_split"):
            verify_admission_inputs(**inputs)

    def test_pnu_requires_ascii_digits(self) -> None:
        locator = copy.deepcopy(make_admission_inputs()["locators"][0])
        locator["pnu"] = "١٢٣٤٥٦٧٨٩٠١٢٣٤٥٦٧٨٩"
        with self.assertRaisesRegex(TargetRosterError, "locator_pnu"):
            SiteLocatorV1.from_dict(locator)

    def test_identity_aliases_are_rejected(self) -> None:
        for token in (
            "site",
            "law",
            "parking",
            "program",
            "geometry",
            "evidence",
            "condition",
            "native",
            "challenged",
            "repeat",
            "prefix",
            "treatment",
            "alias",
        ):
            with self.subTest(token=token):
                spec = copy.deepcopy(make_admission_inputs()["target_specs"][0])
                spec["normalized_subject_identity"] = f"subject-{token}-alias"
                spec["target_spec_sha256"] = canonical_sha256(
                    spec, omit=frozenset({"target_spec_sha256"})
                )
                with self.assertRaisesRegex(
                    TargetRosterError, "normalized_subject_identity"
                ):
                    TargetSpecV1.from_dict(spec)

    def test_raw_byte_length_and_hash_mismatch_are_rejected(self) -> None:
        for field, value in (("byte_length", 0), ("sha256", "0" * 64)):
            with self.subTest(field=field):
                inputs = make_admission_inputs()
                inputs["source_captures"][0][field] = value
                with self.assertRaisesRegex(
                    TargetRosterError, "source_capture_bytes_mismatch"
                ):
                    verify_admission_inputs(**inputs)

    def test_locator_source_reference_and_order_are_closed(self) -> None:
        inputs = make_admission_inputs()
        inputs["locators"][0]["source_capture_ids"] = ("missing-source",)
        inputs["blind_check"]["locator_set_sha256"] = set_digest(inputs["locators"])
        inputs["blind_check"]["record_sha256"] = canonical_sha256(
            inputs["blind_check"], omit=frozenset({"record_sha256"})
        )
        with self.assertRaisesRegex(
            TargetRosterError, "source_capture_reference_missing"
        ):
            verify_admission_inputs(**inputs)
        locator = copy.deepcopy(make_admission_inputs()["locators"][0])
        locator["source_capture_ids"] = ("z", "a")
        with self.assertRaisesRegex(TargetRosterError, "locator_source_capture_ids"):
            SiteLocatorV1.from_dict(locator)

    def test_exact_three_locator_and_thirty_four_target_closures_are_required(
        self,
    ) -> None:
        inputs = make_admission_inputs()
        inputs["locators"].pop()
        with self.assertRaisesRegex(TargetRosterError, "site_locator_count"):
            verify_admission_inputs(**inputs)
        roster = make_roster()
        roster["targets"] = roster["targets"][:-1]
        roster["target_count"] = 33
        with self.assertRaisesRegex(TargetRosterError, "target_count"):
            verify_target_roster(reseal(roster, "roster_sha256"))

    def test_geometry_receipt_set_requires_hard_pass(self) -> None:
        receipt = copy.deepcopy(make_admission_inputs()["geometry_receipts"][0])
        receipt["hard_pass"] = False
        receipt["receipt_sha256"] = canonical_sha256(
            receipt, omit=frozenset({"receipt_sha256"})
        )
        with self.assertRaisesRegex(TargetRosterError, "geometry_receipt_hard_pass"):
            verify_geometry_receipt_set([receipt])

    def test_non_json_self_hash_fields_raise_stable_blockers(self) -> None:
        spec = copy.deepcopy(make_admission_inputs()["target_specs"][0])
        spec["schema_version"] = object()
        with self.assertRaisesRegex(TargetRosterError, "target_spec_sha256"):
            TargetSpecV1.from_dict(spec)
        receipt = copy.deepcopy(make_admission_inputs()["geometry_receipts"][0])
        receipt["schema_version"] = object()
        with self.assertRaisesRegex(TargetRosterError, "geometry_receipt_sha256"):
            GeometryReceiptV1.from_dict(receipt)


class TargetRosterBuilderTests(unittest.TestCase):
    def test_builder_writes_only_to_fresh_output_and_emits_exact_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            input_root = write_complete_inputs(Path(tmp) / "input")
            output_root = Path(tmp) / "output"
            receipt = build_frozen_roster(input_root, output_root)
            self.assertIsInstance(receipt, FreezeReceiptV2)
            self.assertEqual(
                (receipt.new_site_count, receipt.new_target_count), (3, 34)
            )
            self.assertEqual(
                (receipt.combined_dev_site_count, receipt.combined_dev_target_count),
                (8, 64),
            )
            self.assertEqual(receipt.allocation, (12, 11, 11))
            self.assertEqual(
                {
                    path.relative_to(output_root).as_posix()
                    for path in output_root.rglob("*")
                    if path.is_file()
                },
                {
                    "public/architecture_target_roster.json",
                    "public/architecture_freeze_receipt.v2.json",
                    "private/site_locators.json",
                    "private/target_specs.json",
                    "private/source_captures.json",
                    "private/geometry_receipts.json",
                    "private/blind_overlap_check.json",
                    "private/independent_review.json",
                },
            )
            published = json.loads(
                (
                    output_root / "public" / "architecture_freeze_receipt.v2.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(FreezeReceiptV2.from_dict(published), receipt)

    def test_successful_release_census_has_only_expected_files_and_directories(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            input_root = write_complete_inputs(Path(tmp) / "input")
            output_root = Path(tmp) / "output"
            build_frozen_roster(input_root, output_root)
            census = {
                path.relative_to(output_root).as_posix(): "directory"
                if path.is_dir()
                else "file"
                for path in output_root.rglob("*")
            }
            self.assertEqual(
                census,
                {
                    "private": "directory",
                    "public": "directory",
                    "public/architecture_target_roster.json": "file",
                    "public/architecture_freeze_receipt.v2.json": "file",
                    "private/site_locators.json": "file",
                    "private/target_specs.json": "file",
                    "private/source_captures.json": "file",
                    "private/geometry_receipts.json": "file",
                    "private/blind_overlap_check.json": "file",
                    "private/independent_review.json": "file",
                },
            )

    def test_builder_leaves_no_partial_release_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            input_root = write_complete_inputs(Path(tmp) / "input", corrupt_source=True)
            output_root = Path(tmp) / "output"
            with self.assertRaisesRegex(
                TargetRosterError, "source_capture_missing_or_changed"
            ):
                build_frozen_roster(input_root, output_root)
            self.assertFalse(output_root.exists())

    def test_preexisting_output_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            input_root = write_complete_inputs(Path(tmp) / "input")
            output_root = Path(tmp) / "output"
            output_root.mkdir()
            sentinel = output_root / "sentinel.txt"
            sentinel.write_bytes(b"preserve-me")
            with self.assertRaisesRegex(TargetRosterError, "output_root"):
                build_frozen_roster(input_root, output_root)
            self.assertEqual(sentinel.read_bytes(), b"preserve-me")

    def test_nested_input_output_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            input_root = write_complete_inputs(Path(tmp) / "input")
            output_root = input_root / "output"
            with self.assertRaisesRegex(TargetRosterError, "root_containment"):
                build_frozen_roster(input_root, output_root)
            self.assertFalse(output_root.exists())

    def test_unexpected_input_entries_and_constructible_link_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, make_entry in (
                (
                    "file",
                    lambda directory: (directory / "unexpected.txt").write_text(
                        "x", encoding="utf-8"
                    ),
                ),
                ("directory", lambda directory: (directory / "unexpected").mkdir()),
            ):
                with self.subTest(name=name):
                    scenario_root = root / name
                    scenario_root.mkdir()
                    input_root = write_complete_inputs(scenario_root / "input")
                    make_entry(input_root)
                    with self.assertRaisesRegex(TargetRosterError, "input_layout"):
                        build_frozen_roster(input_root, scenario_root / "output")
            link_root = root / "link"
            link_root.mkdir()
            input_root = write_complete_inputs(link_root / "input")
            link = input_root / "unexpected-link"
            try:
                link.symlink_to(input_root / "legacy_bindings.json")
            except OSError:
                self.skipTest("symbolic links are unavailable in this environment")
            with self.assertRaisesRegex(TargetRosterError, "input_layout"):
                build_frozen_roster(input_root, link_root / "output")

    def test_invalid_independent_review_fails_before_staging(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_root = write_complete_inputs(root / "input")
            review_path = input_root / "independent_review.json"
            review = json.loads(review_path.read_text(encoding="utf-8"))
            review["status"] = "rejected"
            review_path.write_text(json.dumps(review), encoding="utf-8", newline="\n")
            output_root = root / "output"
            with self.assertRaisesRegex(TargetRosterError, "independent_review"):
                build_frozen_roster(input_root, output_root)
            self.assertFalse(output_root.exists())
            self.assertEqual({path.name for path in root.iterdir()}, {"input"})

    def test_publication_failure_cleans_fresh_staging(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_root = write_complete_inputs(root / "input")
            output_root = root / "output"
            with patch.object(
                roster_builder, "_windows_move_file_ex_w", return_value=(False, 5)
            ):
                with self.assertRaisesRegex(TargetRosterError, "publication_failed"):
                    build_frozen_roster(input_root, output_root)
            self.assertFalse(output_root.exists())
            self.assertEqual({path.name for path in root.iterdir()}, {"input"})

    def test_race_created_destination_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_root = write_complete_inputs(root / "input")
            output_root = root / "output"

            def create_competing_destination(
                source: str, destination: str, flags: int
            ) -> tuple[bool, int]:
                destination_path = Path(destination)
                destination_path.mkdir()
                (destination_path / "sentinel.txt").write_bytes(b"race-winner")
                return False, 183

            with patch.object(
                roster_builder,
                "_windows_move_file_ex_w",
                side_effect=create_competing_destination,
            ):
                with self.assertRaisesRegex(
                    TargetRosterError, "publication_destination_exists"
                ):
                    build_frozen_roster(input_root, output_root)
            self.assertEqual(
                (output_root / "sentinel.txt").read_bytes(), b"race-winner"
            )
            self.assertEqual(
                {path.name for path in root.iterdir()}, {"input", "output"}
            )

    def test_windows_publication_helper_uses_write_through_without_replace(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            staging_root = root / ".staging"
            output_root = root / "output"
            staging_root.mkdir()
            with patch.object(
                roster_builder, "_windows_move_file_ex_w", return_value=(True, 0)
            ) as mover:
                roster_builder._publish_fresh_directory(staging_root, output_root)
            mover.assert_called_once_with(
                str(staging_root),
                str(output_root),
                roster_builder._MOVEFILE_WRITE_THROUGH,
            )
            self.assertEqual(roster_builder._MOVEFILE_WRITE_THROUGH, 0x8)
            self.assertEqual(roster_builder._MOVEFILE_WRITE_THROUGH & 0x1, 0)

    def test_release_records_require_exact_fields_and_bindings(self) -> None:
        legacy = make_legacy_bindings()
        self.assertEqual(
            LegacyBindingsV1.from_dict(legacy).existing_dev_target_count, 30
        )
        inputs = make_admission_inputs()
        binding = verify_admission_inputs(**inputs)
        admission_hash = canonical_sha256(
            {field.name: getattr(binding, field.name) for field in fields(binding)}
        )
        review = {
            "schema_version": "ace.iclr2027.architecture_independent_review.v1",
            "reviewed_target_roster_sha256": binding.target_roster_sha256,
            "reviewed_admission_binding_sha256": admission_hash,
            "status": "approved",
            "reviewer_identity_commitment": digest("independent-reviewer"),
            "review_sha256": "",
        }
        review["review_sha256"] = canonical_sha256(
            review, omit=frozenset({"review_sha256"})
        )
        self.assertEqual(IndependentReviewV1.from_dict(review).status, "approved")
        legacy["existing_dev_site_count"] = 4
        with self.assertRaisesRegex(TargetRosterError, "legacy_bindings"):
            LegacyBindingsV1.from_dict(legacy)


class TargetRosterDatasetIntegrationTests(unittest.TestCase):
    _LEGACY_PINS = {
        "site_registry.json": (
            7187,
            "8da7fd613c7e8f5e9ccbb2e5673446a1622f06795991dcd971370dd821b0ff91",
        ),
        "split_manifest.json": (
            976,
            "3e4be5febda1dedd4f4598ca5ef6b9d713757330c9563abd357e9c13465dccb6",
        ),
        "site_registry.public.json": (
            1488,
            "2bfbd42fdf82979b56966e80c26d803a6dc232ec39798de236295f94863d9573",
        ),
        "freeze_receipt.json": (
            559,
            "b2a942a4a100755e38b653b212059fd6e5c4237ea26adb29dab330d2e6dd128f",
        ),
        "cases/dev.challenged.manifest.json": (
            2849,
            "eaa3fce318b3843c633052c64e35d3107e5f81b3aecd23779cbc993b30ae3082",
        ),
        "cases/dev.native.manifest.json": (
            2833,
            "1cabfe5ebc42fa32eb750781866ab40568ae7f41364bf9cc3fc022d0c18e5178",
        ),
        "cases/test.challenged.manifest.json": (
            2853,
            "8f3ec5e1abe382ee7bad136d802d17245bb96d383cba2f7b88914312306a1b86",
        ),
        "cases/test.native.manifest.json": (
            2837,
            "984690f09f68a565ff9d65bffb95f7e2b8254ca1b47dc649b4f8877438430e1e",
        ),
    }

    @staticmethod
    def _write_canonical_json(path: Path, payload: object) -> None:
        path.write_text(
            json.dumps(
                payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def _build_release(self, root: Path) -> tuple[Path, Path, str]:
        input_root = write_complete_inputs(root / "input")
        output_root = root / "release"
        build_frozen_roster(input_root, output_root)
        roster_path = output_root / "public" / "architecture_target_roster.json"
        receipt_path = output_root / "public" / "architecture_freeze_receipt.v2.json"
        roster = json.loads(roster_path.read_text(encoding="utf-8"))
        return roster_path, receipt_path, roster["projection_identity_commitment"]

    def test_verified_sidecar_reports_development_target_count_without_legacy_drift(
        self,
    ) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        legacy_root = repository_root / "data" / "iclr2027"
        legacy_bytes = {
            relative: (legacy_root / relative).read_bytes()
            for relative in self._LEGACY_PINS
        }
        for relative, (expected_size, expected_hash) in self._LEGACY_PINS.items():
            with self.subTest(pin=relative):
                self.assertEqual(len(legacy_bytes[relative]), expected_size)
                self.assertEqual(
                    hashlib.sha256(legacy_bytes[relative]).hexdigest(), expected_hash
                )

        registry = json.loads(legacy_bytes["site_registry.json"])
        self.assertEqual(PROGRAM_ORDER, ("neighborhood", "gymnasium", "cultural"))
        self.assertEqual(
            registry_expected_bundle_counts(registry),
            {
                "dev.challenged": 15,
                "dev.native": 15,
                "test.challenged": 15,
                "test.native": 15,
            },
        )
        self.assertEqual(
            sum(
                registry_expected_bundle_counts(registry)[key]
                for key in ("dev.native", "dev.challenged")
            ),
            30,
        )
        commitment = digest("sidecar-absent")
        self.assertIsNone(
            verified_development_target_count(
                target_roster_path=None,
                target_roster_receipt_path=None,
                projection_identity_commitment=commitment,
            )
        )

        with tempfile.TemporaryDirectory() as tmp:
            roster_path, receipt_path, commitment = self._build_release(Path(tmp))
            self.assertEqual(
                verified_development_target_count(
                    target_roster_path=roster_path,
                    target_roster_receipt_path=receipt_path,
                    projection_identity_commitment=commitment,
                ),
                64,
            )
            self.assertEqual(
                verify_frozen_target_roster(
                    roster_path, receipt_path, projection_identity_commitment=commitment
                ).combined_dev_target_count,
                64,
            )

        for relative, expected in legacy_bytes.items():
            with self.subTest(legacy_unchanged=relative):
                self.assertEqual((legacy_root / relative).read_bytes(), expected)

    def test_precall_counts_are_derived_from_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            roster_path, receipt_path, commitment = self._build_release(Path(tmp))
            verifier = getattr(
                precall_design_lock, "verify_architecture_inventory_receipt", None
            )
            view_type = getattr(
                precall_design_lock, "VerifiedArchitectureInventoryV2", None
            )
            self.assertIsNotNone(verifier)
            self.assertIsNotNone(view_type)
            view = verifier(
                roster_path,
                receipt_path,
                projection_identity_commitment=commitment,
            )
            self.assertEqual(
                tuple(field.name for field in fields(view_type)),
                (
                    "schema_version",
                    "site_count",
                    "target_unit_count",
                    "target_roster_sha256",
                    "freeze_receipt_sha256",
                    "projection_identity_commitment",
                    "view_sha256",
                ),
            )
            self.assertEqual((view.site_count, view.target_unit_count), (8, 64))
            self.assertEqual(view_type.from_dict(view.to_dict()), view)

    def test_precall_inventory_adapter_annotations_resolve(self) -> None:
        verifier = getattr(
            precall_design_lock, "verify_architecture_inventory_receipt", None
        )
        self.assertIsNotNone(verifier)
        hints = get_type_hints(verifier)
        self.assertIs(hints["roster_path"], Any)
        self.assertIs(hints["receipt_path"], Any)

    def test_precall_inventory_view_is_receipt_bound(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            roster_path, receipt_path, commitment = self._build_release(Path(tmp))
            verifier = precall_design_lock.verify_architecture_inventory_receipt
            view = verifier(
                roster_path,
                receipt_path,
                projection_identity_commitment=commitment,
            )
            receipt = verify_frozen_target_roster(
                roster_path,
                receipt_path,
                projection_identity_commitment=commitment,
            )
            self.assertEqual(
                view.schema_version,
                "ace.iclr2027.verified_architecture_inventory.v2",
            )
            self.assertEqual((view.site_count, view.target_unit_count), (8, 64))
            self.assertEqual(view.target_roster_sha256, receipt.target_roster_sha256)
            self.assertEqual(view.freeze_receipt_sha256, receipt.receipt_sha256)
            self.assertEqual(view.projection_identity_commitment, commitment)
            self.assertEqual(receipt.projection_identity_commitment, commitment)
            unsigned_view = {
                "schema_version": view.schema_version,
                "site_count": view.site_count,
                "target_unit_count": view.target_unit_count,
                "target_roster_sha256": view.target_roster_sha256,
                "freeze_receipt_sha256": view.freeze_receipt_sha256,
                "projection_identity_commitment": view.projection_identity_commitment,
            }
            self.assertEqual(
                hashlib.sha256(
                    json.dumps(
                        unsigned_view,
                        ensure_ascii=False,
                        allow_nan=False,
                        separators=(",", ":"),
                        sort_keys=True,
                    ).encode("utf-8")
                ).hexdigest(),
                view.view_sha256,
            )
            self.assertTrue(
                {
                    "authority_mode",
                    "status",
                    "official_result_eligible",
                    "candidate_ref",
                    "gate_checks",
                }.isdisjoint(field.name for field in fields(view))
            )
            with self.assertRaises(TargetRosterError):
                verifier(
                    roster_path,
                    receipt_path,
                    projection_identity_commitment=digest("wrong-projection"),
                )

    def test_roster_does_not_upgrade_authenticated_authority(self) -> None:
        with self.assertRaisesRegex(
            NeedsContextError, "authenticated launcher capability is absent"
        ):
            require_authenticated_pre_call_authority()

    def test_verified_sidecar_rejects_all_receipt_and_file_mutations_before_count(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            roster_path, receipt_path, commitment = self._build_release(root)
            original_roster = roster_path.read_text(encoding="utf-8")
            original_receipt = receipt_path.read_text(encoding="utf-8")

            def reject(label: str, mutate: object) -> None:
                roster_path.write_text(original_roster, encoding="utf-8", newline="\n")
                receipt_path.write_text(
                    original_receipt, encoding="utf-8", newline="\n"
                )
                mutate()
                with self.subTest(mutation=label):
                    with self.assertRaises(TargetRosterError):
                        verified_development_target_count(
                            target_roster_path=roster_path,
                            target_roster_receipt_path=receipt_path,
                            projection_identity_commitment=commitment,
                        )

            def mutate_roster_content() -> None:
                roster = json.loads(original_roster)
                roster["targets"][0]["program"] = "changed-program"
                self._write_canonical_json(roster_path, roster)

            def mutate_roster_self_hash() -> None:
                roster = json.loads(original_roster)
                roster["roster_sha256"] = "0" * 64
                self._write_canonical_json(roster_path, roster)

            def mutate_receipt_self_hash() -> None:
                receipt = json.loads(original_receipt)
                receipt["receipt_sha256"] = "0" * 64
                self._write_canonical_json(receipt_path, receipt)

            def mutate_public_site_set_hash() -> None:
                receipt = json.loads(original_receipt)
                receipt["public_site_set_sha256"] = "0" * 64
                receipt["receipt_sha256"] = canonical_sha256(
                    receipt, omit=frozenset({"receipt_sha256"})
                )
                self._write_canonical_json(receipt_path, receipt)

            def mutate_public_target_set_hash() -> None:
                receipt = json.loads(original_receipt)
                receipt["public_target_set_sha256"] = "0" * 64
                receipt["receipt_sha256"] = canonical_sha256(
                    receipt, omit=frozenset({"receipt_sha256"})
                )
                self._write_canonical_json(receipt_path, receipt)

            reject("roster_content", mutate_roster_content)
            reject("roster_self_hash", mutate_roster_self_hash)
            reject("receipt_self_hash", mutate_receipt_self_hash)
            reject("public_site_set_hash", mutate_public_site_set_hash)
            reject("public_target_set_hash", mutate_public_target_set_hash)

            with self.assertRaisesRegex(ValueError, "supplied together"):
                verified_development_target_count(
                    target_roster_path=roster_path,
                    target_roster_receipt_path=None,
                    projection_identity_commitment=commitment,
                )
            with self.assertRaisesRegex(ValueError, "supplied together"):
                verified_development_target_count(
                    target_roster_path=None,
                    target_roster_receipt_path=receipt_path,
                    projection_identity_commitment=commitment,
                )
            with self.assertRaises(TargetRosterError):
                verified_development_target_count(
                    target_roster_path=roster_path,
                    target_roster_receipt_path=receipt_path,
                    projection_identity_commitment=digest("wrong-projection"),
                )

            roster_path.write_text(
                original_roster + "\n", encoding="utf-8", newline="\n"
            )
            receipt_path.write_text(original_receipt, encoding="utf-8", newline="\n")
            with self.assertRaises(TargetRosterError):
                verify_frozen_target_roster(
                    roster_path, receipt_path, projection_identity_commitment=commitment
                )

            roster_path.write_text(original_roster, encoding="utf-8", newline="\n")
            receipt_path.write_text(
                original_receipt + " ", encoding="utf-8", newline="\n"
            )
            with self.assertRaises(TargetRosterError):
                verify_frozen_target_roster(
                    roster_path, receipt_path, projection_identity_commitment=commitment
                )

            roster_path.write_text(original_roster, encoding="utf-8", newline="\n")
            receipt_path.write_text(original_receipt, encoding="utf-8", newline="\n")
            symlink_path = root / "roster-link.json"
            try:
                symlink_path.symlink_to(roster_path)
            except OSError:
                self.skipTest("symbolic links are unavailable in this environment")
            with self.assertRaises(TargetRosterError):
                verify_frozen_target_roster(
                    symlink_path,
                    receipt_path,
                    projection_identity_commitment=commitment,
                )


class TargetRosterRunnerTests(unittest.TestCase):
    _V2_IDENTITY_FIELDS = (
        "schema_version",
        "input_mode",
        "split",
        "patterns",
        "repeats",
        "model",
        "code_commit",
        "case_count",
        "expected_case_count",
        "planned_run_count",
        "stage_case_counts",
        "decision_case_counts",
        "input_hashes",
        "identity_commitment",
        "registry_core_sha256",
        "split_manifest_sha256",
        "plan_sha256",
    )
    _V3_RECEIPT_FIELDS = (
        "target_roster_sha256",
        "target_roster_receipt_sha256",
        "combined_dev_target_count",
    )

    @staticmethod
    def _runner_args(
        checkpoint: Path,
        *,
        roster: Path | None = None,
        receipt: Path | None = None,
        split: str = "dev",
        allow_unfrozen: bool = False,
    ) -> list[str]:
        repository_root = Path(__file__).resolve().parents[1]
        data_root = repository_root / "data" / "iclr2027"
        args = [
            "--split",
            split,
            "--dry-run",
            "--checkpoint-dir",
            str(checkpoint),
            "--registry",
            str(data_root / "site_registry.json"),
            "--split-manifest",
            str(data_root / "split_manifest.json"),
            "--projection-identity",
            str(data_root / "projection_identity.private.json"),
            "--public-registry",
            str(data_root / "site_registry.public.json"),
            "--freeze-receipt",
            str(data_root / "freeze_receipt.json"),
            "--code-commit",
            "runner-v3-pin",
        ]
        if allow_unfrozen:
            args.extend(("--allow-unfrozen", "--cases-dir", str(data_root / "cases")))
        if roster is not None:
            args.extend(("--target-roster", str(roster)))
        if receipt is not None:
            args.extend(("--target-roster-receipt", str(receipt)))
        return args

    @staticmethod
    def _run(args: list[str]) -> int:
        with patch.object(
            architecture_runner,
            "_bind_runtime_dependencies",
            side_effect=lambda value: value,
        ):
            return architecture_runner.main(args)

    @staticmethod
    def _write_canonical(path: Path, payload: object) -> None:
        path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def test_exact_v2_no_sidecar_bytes_and_identity_remain_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint = Path(tmp) / "checkpoint"
            args = self._runner_args(checkpoint)
            args[args.index("runner-v3-pin")] = "legacy-pin"
            code = architecture_runner.main(args)

            raw = (checkpoint / "run_manifest.json").read_bytes()
            manifest = json.loads(raw)
            self.assertEqual(code, 0)
            self.assertEqual(len(raw), 1702)
            self.assertEqual(
                hashlib.sha256(raw).hexdigest(),
                "200fcaf552f83d528b3955143af8d02dbca366a455566171c9aafe241e4cc310",
            )
            self.assertEqual(
                manifest["schema_version"], "ace.iclr2027.exp08_run_manifest.v2"
            )
            self.assertEqual(manifest["case_count"], 30)
            self.assertEqual(
                tuple(run_manifest_identity(manifest)), self._V2_IDENTITY_FIELDS
            )
            self.assertTrue(set(self._V3_RECEIPT_FIELDS).isdisjoint(manifest))

    def test_dry_run_binds_verified_roster_without_model_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            roster_path, receipt_path = build_runner_sidecar(root / "sidecar")
            checkpoint = root / "checkpoint"
            verified = verify_frozen_target_roster(
                roster_path,
                receipt_path,
                projection_identity_commitment=json.loads(
                    receipt_path.read_text(encoding="utf-8")
                )["projection_identity_commitment"],
            )
            with (
                patch.object(
                    architecture_runner,
                    "_bind_runtime_dependencies",
                    side_effect=lambda value: value,
                ),
                patch.object(
                    architecture_runner.ExperimentRunner,
                    "run_single",
                    side_effect=AssertionError("dry run launched a model"),
                ) as run_single,
            ):
                code = architecture_runner.main(
                    self._runner_args(
                        checkpoint, roster=roster_path, receipt=receipt_path
                    )
                )

            manifest = json.loads(
                (checkpoint / "run_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(code, 0)
            self.assertEqual(run_single.call_count, 0)
            self.assertEqual(
                manifest["schema_version"], "ace.iclr2027.exp08_run_manifest.v3"
            )
            self.assertEqual(manifest["case_count"], 30)
            self.assertEqual(manifest["expected_case_count"], 30)
            self.assertEqual(manifest["combined_dev_target_count"], 64)
            self.assertEqual(
                manifest["target_roster_sha256"], verified.target_roster_sha256
            )
            self.assertEqual(
                manifest["target_roster_receipt_sha256"], verified.receipt_sha256
            )

    def test_manifest_invalid_model_fails_before_checkpoint_creation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            roster_path, receipt_path = build_runner_sidecar(root / "sidecar")
            checkpoint = root / "checkpoint"
            args = self._runner_args(
                checkpoint, roster=roster_path, receipt=receipt_path
            )
            args.extend(("--model", "private-model"))

            with self.assertRaisesRegex(ValueError, "private or path-like content"):
                self._run(args)
            self.assertFalse(checkpoint.exists())

    def test_v3_planned_and_executed_identity_is_exact_and_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            roster_path, receipt_path = build_runner_sidecar(root / "sidecar")
            checkpoint = root / "checkpoint"
            self._run(
                self._runner_args(checkpoint, roster=roster_path, receipt=receipt_path)
            )
            planned = json.loads(
                (checkpoint / "run_manifest.json").read_text(encoding="utf-8")
            )
            planned_identity = run_manifest_identity(planned)
            executed = validate_run_manifest(
                {
                    **planned_identity,
                    "executed": True,
                    "execution": {
                        "completed_runs": planned["planned_run_count"],
                        "skipped_runs": 0,
                        "error_runs": 0,
                        "parsed_states": 0,
                        "successful_parses": 0,
                    },
                    "estimated_cost_per_run_usd": 0.0,
                    "estimated_total_cost_usd": 0.0,
                    "estimated_completion_date": "2026-09-01",
                }
            )

            self.assertEqual(
                tuple(planned_identity),
                self._V2_IDENTITY_FIELDS + self._V3_RECEIPT_FIELDS,
            )
            self.assertEqual(run_manifest_identity(executed), planned_identity)
            for field in self._V3_RECEIPT_FIELDS:
                self.assertEqual(executed[field], planned[field])

            invalid_manifests = []
            for field, value in (
                ("input_mode", "public_fixture"),
                ("split", "test"),
                ("combined_dev_target_count", 63),
                ("identity_commitment", None),
                ("target_roster_sha256", None),
            ):
                invalid = copy.deepcopy(planned)
                invalid[field] = value
                invalid_manifests.append(invalid)
            missing = copy.deepcopy(planned)
            missing.pop("target_roster_receipt_sha256")
            invalid_manifests.append(missing)
            v2_with_sidecar_fields = copy.deepcopy(planned)
            v2_with_sidecar_fields["schema_version"] = (
                "ace.iclr2027.exp08_run_manifest.v2"
            )
            invalid_manifests.append(v2_with_sidecar_fields)
            for invalid in invalid_manifests:
                with self.assertRaises(ValueError):
                    validate_run_manifest(invalid)

    def test_invalid_sidecar_modes_fail_before_checkpoint_creation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            roster_path, receipt_path = build_runner_sidecar(root / "sidecar")
            scenarios = (
                self._runner_args(root / "roster-only", roster=roster_path),
                self._runner_args(root / "receipt-only", receipt=receipt_path),
                self._runner_args(
                    root / "public-fixture",
                    roster=roster_path,
                    receipt=receipt_path,
                    allow_unfrozen=True,
                ),
                self._runner_args(
                    root / "test-split",
                    roster=roster_path,
                    receipt=receipt_path,
                    split="test",
                ),
            )
            for args in scenarios:
                checkpoint = Path(args[args.index("--checkpoint-dir") + 1])
                with self.subTest(checkpoint=checkpoint.name):
                    with self.assertRaises(ValueError):
                        self._run(args)
                    self.assertFalse(checkpoint.exists())

            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["projection_identity_commitment"] = "0" * 64
            receipt["receipt_sha256"] = canonical_sha256(
                receipt, omit=frozenset({"receipt_sha256"})
            )
            self._write_canonical(receipt_path, receipt)
            mismatch_checkpoint = root / "projection-mismatch"
            with self.assertRaises(TargetRosterError):
                self._run(
                    self._runner_args(
                        mismatch_checkpoint,
                        roster=roster_path,
                        receipt=receipt_path,
                    )
                )
            self.assertFalse(mismatch_checkpoint.exists())

    def test_unverified_sidecar_fails_before_checkpoint_creation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            roster_path, receipt_path = build_runner_sidecar(root / "sidecar")
            roster_path.write_bytes(roster_path.read_bytes() + b" ")
            checkpoint = root / "checkpoint"
            with self.assertRaises(TargetRosterError):
                self._run(
                    self._runner_args(
                        checkpoint, roster=roster_path, receipt=receipt_path
                    )
                )
            self.assertFalse(checkpoint.exists())

    def test_checkpoint_resume_rejects_changed_roster_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            roster_path, receipt_path = build_runner_sidecar(root / "sidecar")
            checkpoint = root / "checkpoint"
            args = self._runner_args(
                checkpoint, roster=roster_path, receipt=receipt_path
            )
            self._run(args)

            roster = json.loads(roster_path.read_text(encoding="utf-8"))
            roster["targets"][0]["route_kind"] = "changed-route"
            roster["roster_sha256"] = canonical_sha256(
                roster, omit=frozenset({"roster_sha256"})
            )
            self._write_canonical(roster_path, roster)
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["target_roster_sha256"] = roster["roster_sha256"]
            receipt["public_target_set_sha256"] = set_digest(roster["targets"])
            receipt["receipt_sha256"] = canonical_sha256(
                receipt, omit=frozenset({"receipt_sha256"})
            )
            self._write_canonical(receipt_path, receipt)

            with self.assertRaisesRegex(ValueError, "use a new --checkpoint-dir"):
                self._run(args)

    def test_checkpoint_resume_rejects_each_v3_identity_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            roster_path, receipt_path = build_runner_sidecar(root / "sidecar")
            checkpoint = root / "checkpoint"
            args = self._runner_args(
                checkpoint, roster=roster_path, receipt=receipt_path
            )
            self._run(args)
            manifest_path = checkpoint / "run_manifest.json"
            original = json.loads(manifest_path.read_text(encoding="utf-8"))

            for field, value in (
                ("target_roster_sha256", "1" * 64),
                ("target_roster_receipt_sha256", "2" * 64),
                ("combined_dev_target_count", 63),
            ):
                with self.subTest(field=field):
                    stale = copy.deepcopy(original)
                    stale[field] = value
                    self._write_canonical(manifest_path, stale)
                    with self.assertRaisesRegex(
                        ValueError, "use a new --checkpoint-dir"
                    ):
                        self._run(args)
            self._write_canonical(manifest_path, original)

    def test_checkpoint_resume_rejects_v2_v3_schema_mixing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            roster_path, receipt_path = build_runner_sidecar(root / "sidecar")
            v2_checkpoint = root / "v2-checkpoint"
            self._run(self._runner_args(v2_checkpoint))
            with self.assertRaisesRegex(ValueError, "use a new --checkpoint-dir"):
                self._run(
                    self._runner_args(
                        v2_checkpoint, roster=roster_path, receipt=receipt_path
                    )
                )

            v3_checkpoint = root / "v3-checkpoint"
            self._run(
                self._runner_args(
                    v3_checkpoint, roster=roster_path, receipt=receipt_path
                )
            )
            with self.assertRaisesRegex(ValueError, "use a new --checkpoint-dir"):
                self._run(self._runner_args(v3_checkpoint))


class TargetRosterMutationClosureTests(unittest.TestCase):
    def test_deterministic_mutation_matrix_rejects_every_attempt(self) -> None:
        attacks: list[tuple[str, str, object, type[BaseException], str]] = []
        set_permutation_invariants: list[tuple[str, object]] = []
        release_surface_invariants: list[tuple[str, object]] = []

        def add(
            family: str,
            label: str,
            attempt: object,
            expected_exception: type[BaseException] = TargetRosterError,
            expected_message: str = "",
        ) -> None:
            attacks.append(
                (family, label, attempt, expected_exception, expected_message)
            )

        def roster_attempt(mutator: object, *, reseal_hash: bool = True) -> object:
            def attempt() -> None:
                roster = make_roster()
                mutator(roster)  # type: ignore[operator]
                if reseal_hash:
                    reseal(roster, "roster_sha256")
                verify_target_roster(roster)

            return attempt

        # Family 1: each public root field and each concrete site/target row field.
        root_mutations = (
            ("schema_version", "ace.invalid.roster.v1", "schema_version", True),
            ("roster_version", "", "roster_version_empty", True),
            (
                "projection_identity_commitment",
                "0" * 63,
                "projection_identity_commitment",
                True,
            ),
            ("split", "train", "split", True),
            ("site_count", 4, "site_count", True),
            ("target_count", 33, "target_count", True),
            ("allocation", (11, 12, 11), "allocation", True),
            ("sites", "omit", "roster_counts", True),
            ("targets", "omit", "roster_counts", True),
            ("roster_sha256", "0" * 64, "roster_sha256", False),
        )
        for field, value, code, reseal_hash in root_mutations:

            def mutate_root(
                roster: dict[str, object],
                *,
                selected_field: str = field,
                selected_value: object = value,
            ) -> None:
                if selected_value == "omit":
                    roster[selected_field] = tuple(roster[selected_field])[:-1]
                else:
                    roster[selected_field] = selected_value

            add(
                "public_roster",
                f"root:{field}",
                roster_attempt(mutate_root, reseal_hash=reseal_hash),
                expected_message=code,
            )

        for site_index in range(3):
            for field, value, code in (
                ("site_ref", "", "site_ref_empty"),
                ("area_bin", "", "area_bin_empty"),
            ):

                def mutate_site_field(
                    roster: dict[str, object],
                    *,
                    row_index: int = site_index,
                    selected_field: str = field,
                    selected_value: object = value,
                ) -> None:
                    roster["sites"][row_index][selected_field] = selected_value

                add(
                    "public_roster",
                    f"site:{site_index:02d}:{field}",
                    roster_attempt(mutate_site_field),
                    expected_message=code,
                )

        target_field_mutations = (
            ("target_ref", "", "target_ref_or_site"),
            ("site_ref", "missing-site", "target_ref_or_site"),
            ("program", "", "program_empty"),
            ("subject_kind", "", "subject_kind_empty"),
            ("attempt_stage", "", "attempt_stage_empty"),
            ("route_kind", "", "route_kind_empty"),
            ("target_spec_sha256", "g" * 64, "target_spec_sha256"),
            ("source_ids", (), "source_ids"),
        )
        for target_index in range(34):
            for field, value, code in target_field_mutations:

                def mutate_target_field(
                    roster: dict[str, object],
                    *,
                    row_index: int = target_index,
                    selected_field: str = field,
                    selected_value: object = value,
                ) -> None:
                    roster["targets"][row_index][selected_field] = selected_value

                add(
                    "public_roster",
                    f"target:{target_index:02d}:{field}",
                    roster_attempt(mutate_target_field),
                    expected_message=code,
                )

        for left in range(2):

            def reorder_sites(
                roster: dict[str, object], *, position: int = left
            ) -> None:
                rows = list(roster["sites"])
                rows[position], rows[position + 1] = rows[position + 1], rows[position]
                roster["sites"] = tuple(rows)

            add(
                "public_roster",
                f"site-order:{left:02d}:{left + 1:02d}",
                roster_attempt(reorder_sites),
                expected_message="site_order",
            )
        for left in range(33):

            def reorder_targets(
                roster: dict[str, object], *, position: int = left
            ) -> None:
                rows = list(roster["targets"])
                rows[position], rows[position + 1] = rows[position + 1], rows[position]
                roster["targets"] = tuple(rows)

            add(
                "public_roster",
                f"target-order:{left:02d}:{left + 1:02d}",
                roster_attempt(reorder_targets),
                expected_message="target_order",
            )
        for target_index in range(34):

            def reorder_public_source_ids(
                roster: dict[str, object], *, row_index: int = target_index
            ) -> None:
                source_ids = list(roster["targets"][row_index]["source_ids"])
                source_ids[0], source_ids[1] = source_ids[1], source_ids[0]
                roster["targets"][row_index]["source_ids"] = tuple(source_ids)

            add(
                "public_roster",
                f"nested-source-order:{target_index:02d}",
                roster_attempt(reorder_public_source_ids),
                expected_message="source_ids",
            )
        for site_index in range(3):

            def duplicate_site(
                roster: dict[str, object], *, row_index: int = site_index
            ) -> None:
                rows = list(roster["sites"])
                rows[row_index] = copy.deepcopy(rows[(row_index + 1) % 3])
                roster["sites"] = tuple(rows)

            def omit_site(
                roster: dict[str, object], *, row_index: int = site_index
            ) -> None:
                rows = list(roster["sites"])
                rows.pop(row_index)
                roster["sites"] = tuple(rows)

            def insert_site(
                roster: dict[str, object], *, row_index: int = site_index
            ) -> None:
                rows = list(roster["sites"])
                rows.insert(row_index, copy.deepcopy(rows[row_index]))
                roster["sites"] = tuple(rows)

            add(
                "public_roster",
                f"site-duplicate:{site_index:02d}",
                roster_attempt(duplicate_site),
                expected_message="site_order",
            )
            add(
                "public_roster",
                f"site-omission:{site_index:02d}",
                roster_attempt(omit_site),
                expected_message="roster_counts",
            )
            add(
                "public_roster",
                f"site-insertion:{site_index:02d}",
                roster_attempt(insert_site),
                expected_message="roster_counts",
            )
        for target_index in range(34):

            def duplicate_target(
                roster: dict[str, object], *, row_index: int = target_index
            ) -> None:
                rows = list(roster["targets"])
                rows[row_index] = copy.deepcopy(rows[(row_index + 1) % 34])
                roster["targets"] = tuple(rows)

            def omit_target(
                roster: dict[str, object], *, row_index: int = target_index
            ) -> None:
                if row_index == 3:
                    roster["roster_version"] = "v1-fixture-00"
                    verify_target_roster(reseal(roster, "roster_sha256"))
                rows = list(roster["targets"])
                rows.pop(row_index)
                roster["targets"] = tuple(rows)

            def insert_target(
                roster: dict[str, object], *, row_index: int = target_index
            ) -> None:
                rows = list(roster["targets"])
                rows.insert(row_index, copy.deepcopy(rows[row_index]))
                roster["targets"] = tuple(rows)

            add(
                "public_roster",
                f"target-duplicate:{target_index:02d}",
                roster_attempt(duplicate_target),
                expected_message="target_ref_duplicate",
            )
            add(
                "public_roster",
                f"target-omission:{target_index:02d}",
                roster_attempt(omit_target),
                expected_message="roster_counts",
            )
            add(
                "public_roster",
                f"target-insertion:{target_index:02d}",
                roster_attempt(insert_target),
                expected_message="roster_counts",
            )

        def cross_site_pairing(roster: dict[str, object]) -> None:
            first = roster["targets"][0]
            second = roster["targets"][12]
            first["site_ref"], second["site_ref"] = (
                second["site_ref"],
                first["site_ref"],
            )

        add(
            "public_roster",
            "cross-site-rebalanced-pairing",
            roster_attempt(cross_site_pairing),
            expected_message="target_site_pairing",
        )

        # Family 2: protected keys and normalized string-value channels.
        leakage_key_attacks = (
            (
                "root-key:pnu",
                lambda roster: roster.__setitem__("pnu", "1234567890123456789"),
            ),
            (
                "site-key:address",
                lambda roster: roster["sites"][0].__setitem__("address", "not-public"),
            ),
            (
                "target-key:condition",
                lambda roster: roster["targets"][0].__setitem__(
                    "condition", "not-public"
                ),
            ),
        )
        for label, mutator in leakage_key_attacks:
            add(
                "public_leakage",
                label,
                roster_attempt(mutator),
                expected_message="protected_identifier",
            )
        leakage_channels = (
            ("root:address", "root", "address-marker"),
            ("site:uri", "site", "https://example.invalid/private"),
            ("target:path", "target", "C:\\private\\capture.json"),
            ("source-list:pnu", "source", "1234567890123456789"),
            ("source-list:condition", "source", "condition-marker"),
            ("source-list:outcome", "source", "outcome-marker"),
            ("source-list:gold", "source", "gold-marker"),
            ("source-list:mutation", "source", "mutation-marker"),
            ("source-list:evidence-family", "source", "geometry"),
            ("source-list:repeat", "source", "repeat-01"),
            ("source-list:alias", "source", "alias-01"),
        )
        for label, channel, value in leakage_channels:

            def mutate_leakage(
                roster: dict[str, object],
                *,
                selected_channel: str = channel,
                selected_value: str = value,
            ) -> None:
                if selected_channel == "root":
                    roster["roster_version"] = selected_value
                elif selected_channel == "site":
                    roster["sites"][0]["area_bin"] = selected_value
                elif selected_channel == "target":
                    roster["targets"][0]["program"] = selected_value
                else:
                    roster["targets"][0]["source_ids"] = (selected_value,)

            add(
                "public_leakage",
                label,
                roster_attempt(mutate_leakage),
                expected_message="protected_identifier",
            )

        base_admission = make_admission_inputs()
        base_captures = base_admission["source_captures"]
        base_raw = base_admission["raw_bytes_by_source_id"]
        self.assertIsInstance(base_captures, list)
        self.assertIsInstance(base_raw, dict)

        # Family 3: each source-capture row field plus bytes and set closure.
        source_field_mutations = (
            ("schema_version", "ace.invalid.source.v1", "source_capture_schema"),
            ("source_id", "", "source_id"),
            ("publisher", "", "source_publisher"),
            ("canonical_uri", "", "source_canonical_uri"),
            ("retrieved_at", "", "source_retrieved_at"),
            ("effective_at", "", "source_effective_at"),
            ("media_type", "", "source_media_type"),
            ("byte_length", -1, "source_capture_byte_length"),
            ("sha256", "0" * 63, "source_sha256"),
            ("etag", 7, "source_etag"),
            ("last_modified", 7, "source_last_modified"),
            ("license", "", "source_license"),
            ("redistribution_status", "", "source_redistribution_status"),
            ("evidence_families", (), "source_evidence_families"),
        )
        for source_index, source in enumerate(base_captures):
            source_id = source["source_id"]
            for field, value, code in source_field_mutations:

                def mutate_source_field(
                    *,
                    row: dict[str, object] = source,
                    selected_field: str = field,
                    selected_value: object = value,
                ) -> None:
                    mutated = copy.deepcopy(row)
                    mutated[selected_field] = selected_value
                    SourceCaptureV1.from_dict(mutated)

                add(
                    "source_captures",
                    f"row:{source_index:03d}:{source_id}:{field}",
                    mutate_source_field,
                    expected_message=code,
                )

            def mutate_source_bytes(
                *, row: dict[str, object] = source, identity: str = source_id
            ) -> None:
                mutated = copy.deepcopy(row)
                verify_source_capture_set(
                    [mutated], {identity: base_raw[identity] + b"!"}
                )

            add(
                "source_captures",
                f"bytes:{source_index:03d}:{source_id}",
                mutate_source_bytes,
                expected_message="source_capture_bytes_mismatch",
            )

            def omit_source(
                *, row_index: int = source_index, identity: str = source_id
            ) -> None:
                inputs = make_admission_inputs()
                inputs["source_captures"].pop(row_index)
                inputs["raw_bytes_by_source_id"].pop(identity)
                verify_admission_inputs(**inputs)

            def duplicate_source(*, row_index: int = source_index) -> None:
                inputs = make_admission_inputs()
                inputs["source_captures"].append(
                    copy.deepcopy(inputs["source_captures"][row_index])
                )
                verify_admission_inputs(**inputs)

            add(
                "source_captures",
                f"omission:{source_index:03d}:{source_id}",
                omit_source,
                expected_message="source_capture_reference_missing",
            )
            add(
                "source_captures",
                f"duplication:{source_index:03d}:{source_id}",
                duplicate_source,
                expected_message="source_capture_id_duplicate",
            )
        for left in range(len(base_captures) - 1):

            def reorder_sources(*, position: int = left) -> None:
                rows = copy.deepcopy(base_captures)
                rows[position], rows[position + 1] = rows[position + 1], rows[position]
                verify_source_capture_set(rows, copy.deepcopy(base_raw))

            set_permutation_invariants.append(
                (f"source_captures:{left:03d}:{left + 1:03d}", reorder_sources)
            )

        def source_closure_extra() -> None:
            verify_source_capture_set(
                copy.deepcopy(base_captures),
                {**copy.deepcopy(base_raw), "extra-source": b"extra"},
            )

        def source_closure_missing() -> None:
            raw = copy.deepcopy(base_raw)
            raw.pop(base_captures[0]["source_id"])
            verify_source_capture_set(copy.deepcopy(base_captures), raw)

        add(
            "source_captures",
            "source-closure:extra-bytes",
            source_closure_extra,
            expected_message="source_capture_bytes_closure",
        )
        add(
            "source_captures",
            "source-closure:missing-bytes",
            source_closure_missing,
            expected_message="source_capture_bytes_closure",
        )
        for label, value in (
            ("duplicate", ("geometry", "geometry")),
            ("order", ("site", "geometry")),
            ("unknown", ("unknown-family",)),
        ):

            def invalid_capture_families(
                *, selected_value: tuple[str, ...] = value
            ) -> None:
                mutated = copy.deepcopy(base_captures[0])
                mutated["evidence_families"] = selected_value
                SourceCaptureV1.from_dict(mutated)

            add(
                "source_captures",
                f"evidence-families:{label}",
                invalid_capture_families,
                expected_message="source_evidence_families",
            )

        # Family 4: every concrete site-locator row field and set mutation.
        base_locators = base_admission["locators"]
        self.assertIsInstance(base_locators, list)
        locator_field_mutations = (
            ("schema_version", "ace.invalid.locator.v1", "site_locator_schema"),
            ("internal_site_id", "", "locator_internal_site_id"),
            ("pnu", "١٢٣٤٥٦٧٨٩٠١٢٣٤٥٦٧٨٩", "locator_pnu"),
            ("split", "train", "locator_split"),
            ("area_bin", "", "locator_area_bin"),
            ("parcel_geometry_sha256", "0" * 63, "locator_parcel_geometry_sha256"),
            ("project_cluster_id", "", "locator_project_cluster_id"),
            ("source_capture_ids", (), "locator_source_capture_ids"),
        )
        for locator_index, locator in enumerate(base_locators):
            identity = locator["internal_site_id"]
            for field, value, code in locator_field_mutations:

                def mutate_locator_field(
                    *,
                    row: dict[str, object] = locator,
                    selected_field: str = field,
                    selected_value: object = value,
                ) -> None:
                    mutated = copy.deepcopy(row)
                    mutated[selected_field] = selected_value
                    SiteLocatorV1.from_dict(mutated)

                add(
                    "site_locators",
                    f"row:{locator_index:02d}:{identity}:{field}",
                    mutate_locator_field,
                    expected_message=code,
                )

            def omit_locator(*, row_index: int = locator_index) -> None:
                rows = copy.deepcopy(base_locators)
                rows.pop(row_index)
                verify_site_locator_set(rows)

            def duplicate_locator(*, row_index: int = locator_index) -> None:
                rows = copy.deepcopy(base_locators)
                rows.append(copy.deepcopy(rows[row_index]))
                verify_site_locator_set(rows)

            add(
                "site_locators",
                f"omission:{locator_index:02d}:{identity}",
                omit_locator,
                expected_message="site_locator_count",
            )
            add(
                "site_locators",
                f"duplication:{locator_index:02d}:{identity}",
                duplicate_locator,
                expected_message="site_locator_count",
            )
        for field in (
            "internal_site_id",
            "pnu",
            "parcel_geometry_sha256",
            "project_cluster_id",
        ):

            def collide_locator(*, selected_field: str = field) -> None:
                rows = copy.deepcopy(base_locators)
                rows[1][selected_field] = rows[0][selected_field]
                verify_site_locator_set(rows)

            add(
                "site_locators",
                f"uniqueness:{field}",
                collide_locator,
                expected_message="site_or_project_cluster_overlap",
            )
        for left in range(2):

            def reorder_locators(*, position: int = left) -> None:
                rows = copy.deepcopy(base_locators)
                rows[position], rows[position + 1] = rows[position + 1], rows[position]
                verify_site_locator_set(rows)

            set_permutation_invariants.append(
                (f"site_locators:{left:02d}:{left + 1:02d}", reorder_locators)
            )
        for locator_index, locator in enumerate(base_locators):

            def reorder_locator_sources(*, row: dict[str, object] = locator) -> None:
                mutated = copy.deepcopy(row)
                mutated["source_capture_ids"] = tuple(
                    reversed(mutated["source_capture_ids"])
                )
                SiteLocatorV1.from_dict(mutated)

            add(
                "site_locators",
                f"nested-source-order:{locator_index:02d}",
                reorder_locator_sources,
                expected_message="locator_source_capture_ids",
            )

        def locator_missing_source() -> None:
            inputs = make_admission_inputs()
            inputs["locators"][0]["source_capture_ids"] = ("missing-source",)
            inputs["blind_check"]["locator_set_sha256"] = set_digest(inputs["locators"])
            inputs["blind_check"]["record_sha256"] = oracle_record_sha256(
                inputs["blind_check"], "record_sha256"
            )
            verify_admission_inputs(**inputs)

        def locator_area_binding() -> None:
            inputs = make_admission_inputs()
            inputs["locators"][0]["area_bin"] = "different-area-bin"
            verify_admission_inputs(**inputs)

        add(
            "site_locators",
            "source-reference:missing",
            locator_missing_source,
            expected_message="source_capture_reference_missing",
        )
        add(
            "site_locators",
            "site-area-binding",
            locator_area_binding,
            expected_message="site_locator_area_bin_binding",
        )

        # Family 5: every target-spec row field and all target/source closures.
        base_specs = base_admission["target_specs"]
        base_roster = verify_target_roster(base_admission["roster"])
        self.assertIsInstance(base_specs, list)
        spec_field_mutations = (
            ("schema_version", "ace.invalid.spec.v1", "target_spec_schema", True),
            ("target_ref", "", "target_spec_target_ref", True),
            (
                "normalized_subject_identity",
                "",
                "normalized_subject_identity",
                True,
            ),
            (
                "evidence_family_sources",
                "omit-family",
                "target_source_coverage_incomplete",
                False,
            ),
            (
                "geometry_receipt_sha256",
                "0" * 63,
                "geometry_receipt_sha256",
                True,
            ),
            ("target_spec_sha256", "0" * 64, "target_spec_sha256", False),
        )
        for spec_index, spec in enumerate(base_specs):
            identity = spec["target_ref"]
            for field, value, code, reseal_spec in spec_field_mutations:

                def mutate_spec_field(
                    *,
                    row: dict[str, object] = spec,
                    selected_field: str = field,
                    selected_value: object = value,
                    should_reseal: bool = reseal_spec,
                ) -> None:
                    mutated = copy.deepcopy(row)
                    if selected_value == "omit-family":
                        del mutated["evidence_family_sources"]["parking"]
                    else:
                        mutated[selected_field] = selected_value
                    if should_reseal:
                        mutated["target_spec_sha256"] = oracle_record_sha256(
                            mutated, "target_spec_sha256"
                        )
                    TargetSpecV1.from_dict(mutated)

                add(
                    "target_specifications",
                    f"row:{spec_index:02d}:{identity}:{field}",
                    mutate_spec_field,
                    expected_message=code,
                )

            for family in ("geometry", "law", "parking", "program", "site"):

                def omit_evidence_family(
                    *, row: dict[str, object] = spec, selected_family: str = family
                ) -> None:
                    mutated = copy.deepcopy(row)
                    del mutated["evidence_family_sources"][selected_family]
                    TargetSpecV1.from_dict(mutated)

                add(
                    "target_specifications",
                    f"family-map:{spec_index:02d}:{identity}:{family}",
                    omit_evidence_family,
                    expected_message="target_source_coverage_incomplete",
                )

                def reorder_family_sources(
                    *,
                    row: dict[str, object] = spec,
                    selected_family: str = family,
                ) -> None:
                    mutated = copy.deepcopy(row)
                    mutated["evidence_family_sources"][selected_family] = tuple(
                        reversed(mutated["evidence_family_sources"][selected_family])
                    )
                    TargetSpecV1.from_dict(mutated)

                add(
                    "target_specifications",
                    f"nested-source-order:{spec_index:02d}:{identity}:{family}",
                    reorder_family_sources,
                    expected_message="target_source_coverage_incomplete",
                )

            def omit_spec(*, row_index: int = spec_index) -> None:
                rows = copy.deepcopy(base_specs)
                rows.pop(row_index)
                verify_target_spec_set(rows, base_roster)

            def duplicate_spec(*, row_index: int = spec_index) -> None:
                rows = copy.deepcopy(base_specs)
                rows.append(copy.deepcopy(rows[row_index]))
                verify_target_spec_set(rows, base_roster)

            add(
                "target_specifications",
                f"omission:{spec_index:02d}:{identity}",
                omit_spec,
                expected_message="target_spec_target_closure",
            )
            add(
                "target_specifications",
                f"duplication:{spec_index:02d}:{identity}",
                duplicate_spec,
                expected_message="target_spec_target_ref_duplicate",
            )
        for token in (
            "site",
            "law",
            "parking",
            "program",
            "geometry",
            "evidence",
            "condition",
            "native",
            "challenged",
            "repeat",
            "prefix",
            "treatment",
            "alias",
        ):

            def identity_alias(*, selected_token: str = token) -> None:
                mutated = copy.deepcopy(base_specs[0])
                mutated["normalized_subject_identity"] = (
                    f"subject-{selected_token}-alias"
                )
                mutated["target_spec_sha256"] = oracle_record_sha256(
                    mutated, "target_spec_sha256"
                )
                TargetSpecV1.from_dict(mutated)

            add(
                "target_specifications",
                f"normalized-identity-alias:{token}",
                identity_alias,
                expected_message="normalized_subject_identity",
            )
        for left in range(33):

            def reorder_specs(*, position: int = left) -> None:
                rows = copy.deepcopy(base_specs)
                rows[position], rows[position + 1] = rows[position + 1], rows[position]
                verify_target_spec_set(rows, base_roster)

            set_permutation_invariants.append(
                (f"target_specs:{left:02d}:{left + 1:02d}", reorder_specs)
            )

        def evidence_family_swap() -> None:
            inputs = make_admission_inputs()
            spec = inputs["target_specs"][0]
            families = spec["evidence_family_sources"]
            families["geometry"], families["law"] = (
                families["law"],
                families["geometry"],
            )
            spec["target_spec_sha256"] = oracle_record_sha256(
                spec, "target_spec_sha256"
            )
            inputs["roster"]["targets"][0]["target_spec_sha256"] = spec[
                "target_spec_sha256"
            ]
            reseal(inputs["roster"], "roster_sha256")
            verify_admission_inputs(**inputs)

        add(
            "target_specifications",
            "evidence-family-source-swap",
            evidence_family_swap,
            expected_message="evidence_family_source_mapping",
        )
        for field in ("program", "subject_kind", "attempt_stage", "route_kind"):

            def invalid_public_spec_dimension(*, selected_field: str = field) -> None:
                roster = make_roster()
                roster["targets"][0][selected_field] = ""
                verify_target_roster(reseal(roster, "roster_sha256"))

            add(
                "target_specifications",
                f"public-dimension:{field}",
                invalid_public_spec_dimension,
                expected_message=f"{field}_empty",
            )

        def target_source_reference_missing() -> None:
            inputs = make_admission_inputs()
            replace_shared_target_source_with_missing(inputs)
            verify_admission_inputs(**inputs)

        add(
            "target_specifications",
            "source-reference:missing",
            target_source_reference_missing,
            expected_message="source_capture_reference_missing",
        )

        # Family 6: every geometry-receipt row field and target closure.
        base_geometry = base_admission["geometry_receipts"]
        self.assertIsInstance(base_geometry, list)
        geometry_field_mutations = (
            ("schema_version", "ace.invalid.geometry.v1", "geometry_receipt_schema"),
            ("target_ref", "", "geometry_receipt_target_ref"),
            ("input_geometry_sha256", "0" * 63, "input_geometry_sha256"),
            (
                "materializer_code_sha256",
                "0" * 63,
                "materializer_code_sha256",
            ),
            ("output_geometry_sha256", "0" * 63, "output_geometry_sha256"),
            ("compile_log_sha256", "0" * 63, "compile_log_sha256"),
            ("hard_pass", False, "geometry_receipt_hard_pass"),
            ("receipt_sha256", "0" * 64, "geometry_receipt_sha256"),
        )
        for receipt_index, receipt in enumerate(base_geometry):
            identity = receipt["target_ref"]
            for field, value, code in geometry_field_mutations:

                def mutate_geometry_field(
                    *,
                    row: dict[str, object] = receipt,
                    selected_field: str = field,
                    selected_value: object = value,
                ) -> None:
                    mutated = copy.deepcopy(row)
                    mutated[selected_field] = selected_value
                    if selected_field != "receipt_sha256":
                        mutated["receipt_sha256"] = oracle_record_sha256(
                            mutated, "receipt_sha256"
                        )
                    verify_geometry_receipt_set([mutated])

                add(
                    "geometry_receipts",
                    f"row:{receipt_index:02d}:{identity}:{field}",
                    mutate_geometry_field,
                    expected_message=code,
                )

            def omit_geometry(*, row_index: int = receipt_index) -> None:
                inputs = make_admission_inputs()
                inputs["geometry_receipts"].pop(row_index)
                verify_admission_inputs(**inputs)

            def duplicate_geometry(*, row_index: int = receipt_index) -> None:
                rows = copy.deepcopy(base_geometry)
                rows.append(copy.deepcopy(rows[row_index]))
                verify_geometry_receipt_set(rows)

            add(
                "geometry_receipts",
                f"omission:{receipt_index:02d}:{identity}",
                omit_geometry,
                expected_message="geometry_receipt_target_closure",
            )
            add(
                "geometry_receipts",
                f"duplication:{receipt_index:02d}:{identity}",
                duplicate_geometry,
                expected_message="geometry_receipt_target_ref_duplicate",
            )
        for left in range(33):

            def reorder_geometry(*, position: int = left) -> None:
                rows = copy.deepcopy(base_geometry)
                rows[position], rows[position + 1] = rows[position + 1], rows[position]
                verify_geometry_receipt_set(rows)

            set_permutation_invariants.append(
                (f"geometry_receipts:{left:02d}:{left + 1:02d}", reorder_geometry)
            )

        # Family 7: blind-overlap record fields, bindings, caller pins, and omission.
        base_blind = base_admission["blind_check"]
        self.assertIsInstance(base_blind, dict)
        blind_field_mutations = (
            ("schema_version", "ace.invalid.blind.v1", True),
            ("locator_set_sha256", "0" * 63, True),
            ("protected_roster_commitment", "0" * 63, True),
            ("overlap_found", True, True),
            ("checked_site_count", 2, True),
            ("audit_sha256", "0" * 63, True),
            ("record_sha256", "0" * 64, False),
        )
        for field, value, reseal_blind in blind_field_mutations:

            def mutate_blind_field(
                *,
                selected_field: str = field,
                selected_value: object = value,
                should_reseal: bool = reseal_blind,
            ) -> None:
                mutated = copy.deepcopy(base_blind)
                mutated[selected_field] = selected_value
                if should_reseal:
                    mutated["record_sha256"] = oracle_record_sha256(
                        mutated, "record_sha256"
                    )
                verify_blind_overlap_check(
                    mutated,
                    locator_set_sha256=base_blind["locator_set_sha256"],
                    protected_roster_commitment=base_blind[
                        "protected_roster_commitment"
                    ],
                )

            add(
                "blind_overlap_check",
                f"field:{field}",
                mutate_blind_field,
                expected_message="blinded_membership_check",
            )

        def blind_wrong_locator_caller() -> None:
            verify_blind_overlap_check(
                copy.deepcopy(base_blind),
                locator_set_sha256=digest("wrong-locator-set"),
                protected_roster_commitment=base_blind["protected_roster_commitment"],
            )

        def blind_wrong_protected_caller() -> None:
            verify_blind_overlap_check(
                copy.deepcopy(base_blind),
                locator_set_sha256=base_blind["locator_set_sha256"],
                protected_roster_commitment=digest("wrong-protected-roster"),
            )

        def blind_omission() -> None:
            inputs = make_admission_inputs()
            inputs["blind_check"] = {}
            verify_admission_inputs(**inputs)

        add(
            "blind_overlap_check",
            "wrong-caller:locator-set",
            blind_wrong_locator_caller,
            expected_message="blinded_membership_check",
        )
        add(
            "blind_overlap_check",
            "wrong-caller:protected-roster",
            blind_wrong_protected_caller,
            expected_message="blinded_membership_check",
        )
        add(
            "blind_overlap_check",
            "omission",
            blind_omission,
            expected_message="blinded_membership_check",
        )

        def write_canonical_json(path: Path, payload: object) -> None:
            path.write_text(
                json.dumps(
                    payload,
                    ensure_ascii=True,
                    allow_nan=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n",
                encoding="utf-8",
                newline="\n",
            )

        def make_review() -> dict[str, object]:
            review: dict[str, object] = {
                "schema_version": "ace.iclr2027.architecture_independent_review.v1",
                "reviewed_target_roster_sha256": digest("reviewed-roster"),
                "reviewed_admission_binding_sha256": digest("reviewed-admission"),
                "status": "approved",
                "reviewer_identity_commitment": digest("reviewer"),
                "review_sha256": "",
            }
            review["review_sha256"] = oracle_record_sha256(review, "review_sha256")
            return review

        # Family 8: every review field, count/allocation smuggling, and pairing.
        review_field_mutations = (
            ("schema_version", "ace.invalid.review.v1", True),
            ("reviewed_target_roster_sha256", "0" * 63, True),
            ("reviewed_admission_binding_sha256", "0" * 63, True),
            ("status", "rejected", True),
            ("reviewer_identity_commitment", "0" * 63, True),
            ("review_sha256", "0" * 64, False),
        )
        for field, value, reseal_review in review_field_mutations:

            def mutate_review_field(
                *,
                selected_field: str = field,
                selected_value: object = value,
                should_reseal: bool = reseal_review,
            ) -> None:
                review = make_review()
                review[selected_field] = selected_value
                if should_reseal:
                    review["review_sha256"] = oracle_record_sha256(
                        review, "review_sha256"
                    )
                IndependentReviewV1.from_dict(review)

            add(
                "independent_review",
                f"field:{field}",
                mutate_review_field,
                expected_message="independent_review",
            )
        for extra_field, value in (
            ("reviewed_target_count", 34),
            ("reviewed_allocation", [12, 11, 11]),
        ):

            def smuggle_review_field(
                *, selected_field: str = extra_field, selected_value: object = value
            ) -> None:
                review = make_review()
                review[selected_field] = selected_value
                review["review_sha256"] = oracle_record_sha256(review, "review_sha256")
                IndependentReviewV1.from_dict(review)

            add(
                "independent_review",
                f"extra:{extra_field}",
                smuggle_review_field,
                expected_message="independent_review",
            )

        def stale_review_binding(field: str) -> None:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                input_root = write_complete_inputs(root / "input")
                review_path = input_root / "independent_review.json"
                review = json.loads(review_path.read_text(encoding="utf-8"))
                review[field] = digest(f"wrong:{field}")
                review["review_sha256"] = oracle_record_sha256(review, "review_sha256")
                write_canonical_json(review_path, review)
                build_frozen_roster(input_root, root / "release")

        for field in (
            "reviewed_target_roster_sha256",
            "reviewed_admission_binding_sha256",
        ):
            add(
                "independent_review",
                f"wrong-pairing:{field}",
                lambda selected_field=field: stale_review_binding(selected_field),
                expected_message="release_binding",
            )

        def make_freeze_receipt(
            roster: dict[str, object] | None = None,
        ) -> dict[str, object]:
            selected_roster = make_roster() if roster is None else roster
            receipt: dict[str, object] = {
                "schema_version": "ace.iclr2027.architecture_freeze_receipt.v2",
                "registry_version": "registry-v1",
                "registry_core_sha256": digest("registry-core"),
                "projection_identity_commitment": selected_roster[
                    "projection_identity_commitment"
                ],
                "split_manifest_sha256": digest("split-manifest"),
                "public_registry_sha256": digest("public-registry"),
                "public_case_set_sha256": digest("public-cases"),
                "site_locator_set_sha256": digest("site-locators"),
                "public_site_set_sha256": set_digest(
                    list(copy.deepcopy(selected_roster["sites"]))
                ),
                "public_target_set_sha256": set_digest(
                    list(copy.deepcopy(selected_roster["targets"]))
                ),
                "source_capture_set_sha256": digest("source-captures"),
                "target_spec_set_sha256": digest("target-specs"),
                "geometry_receipt_set_sha256": digest("geometry-receipts"),
                "target_roster_sha256": selected_roster["roster_sha256"],
                "new_site_count": 3,
                "new_target_count": 34,
                "allocation": [12, 11, 11],
                "combined_dev_site_count": 8,
                "combined_dev_target_count": 64,
                "blind_overlap_check_sha256": digest("blind-overlap"),
                "independent_review_sha256": digest("independent-review"),
                "receipt_sha256": "",
            }
            receipt["receipt_sha256"] = oracle_record_sha256(receipt, "receipt_sha256")
            return receipt

        # Family 9: all exact 22 fields and public frozen-file bindings.
        base_receipt = make_freeze_receipt()
        receipt_hash_fields = {
            "registry_core_sha256",
            "projection_identity_commitment",
            "split_manifest_sha256",
            "public_registry_sha256",
            "public_case_set_sha256",
            "site_locator_set_sha256",
            "public_site_set_sha256",
            "public_target_set_sha256",
            "source_capture_set_sha256",
            "target_spec_set_sha256",
            "geometry_receipt_set_sha256",
            "target_roster_sha256",
            "blind_overlap_check_sha256",
            "independent_review_sha256",
            "receipt_sha256",
        }
        receipt_count_fields = {
            "new_site_count",
            "new_target_count",
            "combined_dev_site_count",
            "combined_dev_target_count",
        }
        for field in tuple(base_receipt):
            if field == "schema_version":
                replacement: object = "ace.invalid.freeze.v2"
            elif field == "registry_version":
                replacement = ""
            elif field in receipt_hash_fields:
                replacement = digest(f"mutated:{field}")
            elif field == "allocation":
                replacement = [11, 12, 11]
            elif field in receipt_count_fields:
                replacement = int(base_receipt[field]) + 1
            else:
                raise AssertionError(f"unclassified receipt field: {field}")

            def mutate_receipt_field(
                *, selected_field: str = field, selected_value: object = replacement
            ) -> None:
                receipt = copy.deepcopy(base_receipt)
                receipt[selected_field] = selected_value
                FreezeReceiptV2.from_dict(receipt)

            add(
                "freeze_receipt_v2",
                f"field:{field}",
                mutate_receipt_field,
                expected_message="freeze_receipt",
            )

        def receipt_extra_field() -> None:
            receipt = copy.deepcopy(base_receipt)
            receipt["extra"] = "forbidden"
            FreezeReceiptV2.from_dict(receipt)

        def receipt_missing_field() -> None:
            receipt = copy.deepcopy(base_receipt)
            del receipt["independent_review_sha256"]
            FreezeReceiptV2.from_dict(receipt)

        add(
            "freeze_receipt_v2",
            "extra-field",
            receipt_extra_field,
            expected_message="freeze_receipt",
        )
        add(
            "freeze_receipt_v2",
            "missing-field:independent_review_sha256",
            receipt_missing_field,
            expected_message="freeze_receipt",
        )

        def frozen_file_attack(
            mutator: object, *, reverse_receipt_keys: bool = False
        ) -> None:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                roster = make_roster()
                receipt = make_freeze_receipt(roster)
                roster_path = root / "roster.json"
                receipt_path = root / "receipt.json"
                mutator(roster, receipt)  # type: ignore[operator]
                write_canonical_json(roster_path, roster)
                if reverse_receipt_keys:
                    receipt_path.write_text(
                        json.dumps(
                            dict(reversed(tuple(receipt.items()))),
                            ensure_ascii=True,
                            separators=(",", ":"),
                        )
                        + "\n",
                        encoding="utf-8",
                        newline="\n",
                    )
                else:
                    write_canonical_json(receipt_path, receipt)
                verify_frozen_target_roster(
                    roster_path,
                    receipt_path,
                    projection_identity_commitment=roster[
                        "projection_identity_commitment"
                    ],
                )

        def mutate_receipt_binding(field: str) -> object:
            def mutate(_roster: dict[str, object], receipt: dict[str, object]) -> None:
                receipt[field] = digest(f"wrong:{field}")
                receipt["receipt_sha256"] = oracle_record_sha256(
                    receipt, "receipt_sha256"
                )

            return mutate

        for field, code in (
            ("target_roster_sha256", "frozen_target_roster_binding"),
            ("public_site_set_sha256", "public_site_set_sha256"),
            ("public_target_set_sha256", "public_target_set_sha256"),
            ("projection_identity_commitment", "projection_identity_commitment"),
        ):
            add(
                "freeze_receipt_v2",
                f"file-binding:{field}",
                lambda selected_field=field: frozen_file_attack(
                    mutate_receipt_binding(selected_field)
                ),
                expected_message=code,
            )

        add(
            "freeze_receipt_v2",
            "canonical-key-order",
            lambda: frozen_file_attack(
                lambda _roster, _receipt: None, reverse_receipt_keys=True
            ),
            expected_message="freeze_receipt_canonical_json",
        )

        def mutate_public_roster_after_receipt(
            roster: dict[str, object], _receipt: dict[str, object]
        ) -> None:
            roster["targets"][0]["route_kind"] = "route-rebound"
            reseal(roster, "roster_sha256")

        add(
            "freeze_receipt_v2",
            "public-roster-mutation-after-receipt",
            lambda: frozen_file_attack(mutate_public_roster_after_receipt),
            expected_message="frozen_target_roster_binding",
        )

        # Family 10: exact builder inputs/source objects and release surface.
        input_names = (
            "legacy_bindings.json",
            "target_roster.json",
            "site_locators.json",
            "target_specs.json",
            "source_captures.json",
            "geometry_receipts.json",
            "blind_overlap_check.json",
            "independent_review.json",
        )

        def builder_input_attack(mutator: object) -> None:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                input_root = write_complete_inputs(root / "input")
                mutator(input_root)  # type: ignore[operator]
                build_frozen_roster(input_root, root / "release")

        for name in input_names:

            def omit_input(input_root: Path, *, selected_name: str = name) -> None:
                (input_root / selected_name).unlink()

            def substitute_input_type(
                input_root: Path, *, selected_name: str = name
            ) -> None:
                path = input_root / selected_name
                path.unlink()
                path.mkdir()

            add(
                "builder_release_surface",
                f"input-omission:{name}",
                lambda mutator=omit_input: builder_input_attack(mutator),
                expected_message="input_layout",
            )
            add(
                "builder_release_surface",
                f"input-type-substitution:{name}",
                lambda mutator=substitute_input_type: builder_input_attack(mutator),
                expected_message="input_layout",
            )

        def extra_input(input_root: Path) -> None:
            (input_root / "extra.json").write_text("{}", encoding="utf-8")

        add(
            "builder_release_surface",
            "input-extra-object",
            lambda: builder_input_attack(extra_input),
            expected_message="input_layout",
        )

        def source_object_attack(kind: str) -> None:
            def mutate(input_root: Path) -> None:
                source_root = input_root / "source_objects"
                source_path = next(source_root.iterdir())
                if kind == "omit":
                    source_path.unlink()
                elif kind == "extra":
                    (source_root / "extra.bin").write_bytes(b"extra")
                elif kind == "bytes":
                    source_path.write_bytes(source_path.read_bytes() + b"!")
                elif kind == "type":
                    source_path.unlink()
                    source_path.mkdir()
                else:
                    raise AssertionError(kind)

            builder_input_attack(mutate)

        for kind, code in (
            ("omit", "source_capture_missing_or_changed"),
            ("extra", "input_layout"),
            ("bytes", "source_capture_missing_or_changed"),
            ("type", "input_layout"),
        ):
            add(
                "builder_release_surface",
                f"source-object:{kind}",
                lambda selected_kind=kind: source_object_attack(selected_kind),
                expected_message=code,
            )

        output_paths = (
            "public/architecture_target_roster.json",
            "public/architecture_freeze_receipt.v2.json",
            "private/site_locators.json",
            "private/target_specs.json",
            "private/source_captures.json",
            "private/geometry_receipts.json",
            "private/blind_overlap_check.json",
            "private/independent_review.json",
        )

        def exact_release_surface() -> None:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                input_root = write_complete_inputs(root / "input")
                release_root = root / "release"
                build_frozen_roster(input_root, release_root)
                observed = {
                    path.relative_to(release_root).as_posix(): (
                        "directory" if path.is_dir() else "file"
                    )
                    for path in release_root.rglob("*")
                }
                expected = {
                    "public": "directory",
                    "private": "directory",
                    **{relative_path: "file" for relative_path in output_paths},
                }
                self.assertEqual(observed, expected)

        release_surface_invariants.append(
            ("builder-emits-exact-eight-files", exact_release_surface)
        )

        def release_output_attack(relative_path: str, kind: str) -> None:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                input_root = write_complete_inputs(root / "input")
                release_root = root / "release"
                build_frozen_roster(input_root, release_root)
                receipt_path = (
                    release_root / "public" / "architecture_freeze_receipt.v2.json"
                )
                projection = json.loads(receipt_path.read_text(encoding="utf-8"))[
                    "projection_identity_commitment"
                ]
                selected = release_root / relative_path
                if kind == "omit":
                    selected.unlink()
                elif kind == "type":
                    selected.unlink()
                    selected.mkdir()
                else:
                    raise AssertionError(kind)
                verify_frozen_target_roster(
                    release_root / "public" / "architecture_target_roster.json",
                    receipt_path,
                    projection_identity_commitment=projection,
                )

        for relative_path in output_paths:
            public_output = relative_path.startswith("public/")
            if not public_output:
                continue
            label = relative_path.replace("/", ":")
            for kind in ("omit", "type"):
                if "target_roster" in relative_path:
                    code = "target_roster_file"
                elif "freeze_receipt" in relative_path:
                    code = "freeze_receipt_file"
                else:
                    code = "release_output_closure"
                add(
                    "builder_release_surface",
                    f"output-{kind}:{label}",
                    lambda path=relative_path,
                    selected_kind=kind: release_output_attack(path, selected_kind),
                    expected_message=code
                    if public_output
                    else "release_output_closure",
                )

        def stale_release_pairing() -> None:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                input_a = write_complete_inputs(root / "input-a")
                release_a = root / "release-a"
                build_frozen_roster(input_a, release_a)

                input_b = write_complete_inputs(root / "input-b")
                roster_path = input_b / "target_roster.json"
                roster = json.loads(roster_path.read_text(encoding="utf-8"))
                roster["roster_version"] = "v2-distinct-release"
                roster["roster_sha256"] = oracle_record_sha256(roster, "roster_sha256")
                write_canonical_json(roster_path, roster)
                captures = json.loads(
                    (input_b / "source_captures.json").read_text(encoding="utf-8")
                )
                raw_bytes = {
                    capture["source_id"]: (
                        input_b / "source_objects" / f"{capture['sha256']}.bin"
                    ).read_bytes()
                    for capture in captures
                }
                blind = json.loads(
                    (input_b / "blind_overlap_check.json").read_text(encoding="utf-8")
                )
                binding = verify_admission_inputs(
                    roster=roster,
                    target_specs=json.loads(
                        (input_b / "target_specs.json").read_text(encoding="utf-8")
                    ),
                    locators=json.loads(
                        (input_b / "site_locators.json").read_text(encoding="utf-8")
                    ),
                    source_captures=captures,
                    raw_bytes_by_source_id=raw_bytes,
                    geometry_receipts=json.loads(
                        (input_b / "geometry_receipts.json").read_text(encoding="utf-8")
                    ),
                    blind_check=blind,
                    protected_roster_commitment=blind["protected_roster_commitment"],
                )
                binding_payload = {
                    "target_roster_sha256": binding.target_roster_sha256,
                    "locator_set_sha256": binding.locator_set_sha256,
                    "source_capture_set_sha256": binding.source_capture_set_sha256,
                    "target_spec_set_sha256": binding.target_spec_set_sha256,
                    "geometry_receipt_set_sha256": binding.geometry_receipt_set_sha256,
                    "blind_overlap_check_sha256": binding.blind_overlap_check_sha256,
                }
                review_path = input_b / "independent_review.json"
                review = json.loads(review_path.read_text(encoding="utf-8"))
                review["reviewed_target_roster_sha256"] = binding.target_roster_sha256
                review["reviewed_admission_binding_sha256"] = oracle_record_sha256(
                    binding_payload, "no-self-hash-field"
                )
                review["review_sha256"] = oracle_record_sha256(review, "review_sha256")
                write_canonical_json(review_path, review)
                release_b = root / "release-b"
                build_frozen_roster(input_b, release_b)

                receipt_b = release_b / "public" / "architecture_freeze_receipt.v2.json"
                projection = json.loads(receipt_b.read_text(encoding="utf-8"))[
                    "projection_identity_commitment"
                ]
                verify_frozen_target_roster(
                    release_a / "public" / "architecture_target_roster.json",
                    receipt_b,
                    projection_identity_commitment=projection,
                )

        add(
            "builder_release_surface",
            "stale-release-pairing",
            stale_release_pairing,
            expected_message="frozen_target_roster_binding",
        )

        # Family 11: resealed lower-layer mutations and all runner-v3 pins.
        def rewrite_input(
            input_root: Path, name: str, mutator: object
        ) -> dict[str, object]:
            path = input_root / name
            payload = json.loads(path.read_text(encoding="utf-8"))
            mutator(payload)  # type: ignore[operator]
            write_canonical_json(path, payload)
            return payload

        def cross_layer_builder(mutator: object) -> None:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                input_root = write_complete_inputs(root / "input")
                mutator(input_root)  # type: ignore[operator]
                build_frozen_roster(input_root, root / "release")

        def reseal_roster_lower(input_root: Path) -> None:
            def mutate(roster: dict[str, object]) -> None:
                roster["roster_version"] = "v2-resealed"
                roster["roster_sha256"] = oracle_record_sha256(roster, "roster_sha256")

            rewrite_input(input_root, "target_roster.json", mutate)

        def mutate_capture_lower(input_root: Path) -> None:
            rewrite_input(
                input_root,
                "source_captures.json",
                lambda rows: rows[0].__setitem__("publisher", "changed-publisher"),
            )

        def reseal_locator_blind_lower(input_root: Path) -> None:
            locators = rewrite_input(
                input_root,
                "site_locators.json",
                lambda rows: rows[0].__setitem__(
                    "project_cluster_id", "changed-cluster"
                ),
            )

            def mutate_blind(blind: dict[str, object]) -> None:
                blind["locator_set_sha256"] = set_digest(locators)
                blind["record_sha256"] = oracle_record_sha256(blind, "record_sha256")

            rewrite_input(input_root, "blind_overlap_check.json", mutate_blind)

        def reseal_spec_lower(input_root: Path) -> None:
            def mutate_specs(specs: list[dict[str, object]]) -> None:
                specs[0]["normalized_subject_identity"] = "rebound-subject-00"
                specs[0]["target_spec_sha256"] = oracle_record_sha256(
                    specs[0], "target_spec_sha256"
                )

            specs = rewrite_input(input_root, "target_specs.json", mutate_specs)

            def mutate_roster(roster: dict[str, object]) -> None:
                roster["targets"][0]["target_spec_sha256"] = specs[0][
                    "target_spec_sha256"
                ]
                roster["roster_sha256"] = oracle_record_sha256(roster, "roster_sha256")

            rewrite_input(input_root, "target_roster.json", mutate_roster)

        def reseal_geometry_lower(input_root: Path) -> None:
            def mutate_receipts(receipts: list[dict[str, object]]) -> None:
                receipts[0]["input_geometry_sha256"] = digest("changed-input-geometry")
                receipts[0]["receipt_sha256"] = oracle_record_sha256(
                    receipts[0], "receipt_sha256"
                )

            receipts = rewrite_input(
                input_root, "geometry_receipts.json", mutate_receipts
            )

            def mutate_specs(specs: list[dict[str, object]]) -> None:
                specs[0]["geometry_receipt_sha256"] = receipts[0]["receipt_sha256"]
                specs[0]["target_spec_sha256"] = oracle_record_sha256(
                    specs[0], "target_spec_sha256"
                )

            specs = rewrite_input(input_root, "target_specs.json", mutate_specs)

            def mutate_roster(roster: dict[str, object]) -> None:
                roster["targets"][0]["target_spec_sha256"] = specs[0][
                    "target_spec_sha256"
                ]
                roster["roster_sha256"] = oracle_record_sha256(roster, "roster_sha256")

            rewrite_input(input_root, "target_roster.json", mutate_roster)

        def reseal_blind_lower(input_root: Path) -> None:
            def mutate(blind: dict[str, object]) -> None:
                blind["audit_sha256"] = digest("changed-blind-audit")
                blind["record_sha256"] = oracle_record_sha256(blind, "record_sha256")

            rewrite_input(input_root, "blind_overlap_check.json", mutate)

        for label, mutator in (
            ("roster-to-review", reseal_roster_lower),
            ("capture-to-review", mutate_capture_lower),
            ("locator-blind-to-review", reseal_locator_blind_lower),
            ("spec-to-review", reseal_spec_lower),
            ("geometry-spec-to-review", reseal_geometry_lower),
            ("blind-to-review", reseal_blind_lower),
        ):
            add(
                "cross_layer_attacks",
                f"resealed:{label}",
                lambda selected_mutator=mutator: cross_layer_builder(selected_mutator),
                expected_message="release_binding",
            )

        def runner_stale_binding(field: str, value: object) -> None:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                roster_path, receipt_path = build_runner_sidecar(root / "sidecar")
                checkpoint = root / "checkpoint"
                args = TargetRosterRunnerTests._runner_args(
                    checkpoint, roster=roster_path, receipt=receipt_path
                )
                TargetRosterRunnerTests._run(args)
                manifest_path = checkpoint / "run_manifest.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest[field] = value
                write_canonical_json(manifest_path, manifest)
                TargetRosterRunnerTests._run(args)

        for field, value in (
            ("target_roster_sha256", "1" * 64),
            ("target_roster_receipt_sha256", "2" * 64),
            ("combined_dev_target_count", 63),
        ):
            add(
                "cross_layer_attacks",
                f"runner-v3-stale:{field}",
                lambda selected_field=field, selected_value=value: runner_stale_binding(
                    selected_field, selected_value
                ),
                ValueError,
                "use a new --checkpoint-dir",
            )

        expected_family_census = {
            "public_roster": 469,
            "public_leakage": 14,
            "source_captures": 2946,
            "site_locators": 39,
            "target_specifications": 631,
            "geometry_receipts": 340,
            "blind_overlap_check": 10,
            "independent_review": 10,
            "freeze_receipt_v2": 30,
            "builder_release_surface": 26,
            "cross_layer_attacks": 9,
        }
        actual_family_census = {
            family: sum(attack[0] == family for attack in attacks)
            for family in expected_family_census
        }
        self.assertEqual(actual_family_census, expected_family_census)

        invariant_failures: list[str] = []
        for label, invariant in set_permutation_invariants:
            try:
                invariant()  # type: ignore[operator]
            except BaseException as exc:  # pragma: no branch - census continues
                invariant_failures.append(f"{label}:{type(exc).__name__}:{exc}")
        for label, invariant in release_surface_invariants:
            try:
                invariant()  # type: ignore[operator]
            except BaseException as exc:  # pragma: no branch - census continues
                invariant_failures.append(f"{label}:{type(exc).__name__}:{exc}")

        accepted: list[str] = []
        wrong_rejections: list[str] = []
        for family, label, attempt, expected_exception, expected_message in attacks:
            identity = f"{family}:{label}"
            try:
                attempt()  # type: ignore[operator]
            except expected_exception as exc:
                if expected_message and expected_message not in str(exc):
                    wrong_rejections.append(
                        f"{identity}:expected={expected_message}:actual={exc}"
                    )
            except BaseException as exc:  # pragma: no branch - census continues
                wrong_rejections.append(
                    f"{identity}:unexpected={type(exc).__name__}:{exc}"
                )
            else:
                accepted.append(identity)

        attempted_count = len(attacks)
        print(
            "MUTATION_CENSUS="
            + json.dumps(actual_family_census, sort_keys=True, separators=(",", ":"))
        )
        print(f"MUTATION_ATTEMPTED={attempted_count}")
        print(f"MUTATION_ACCEPTED={len(accepted)}")
        print(f"SET_PERMUTATION_INVARIANTS={len(set_permutation_invariants)}")
        print(f"RELEASE_SURFACE_INVARIANTS={len(release_surface_invariants)}")
        if accepted:
            print(
                "ACCEPTED_MUTATIONS="
                + json.dumps(accepted, ensure_ascii=True, separators=(",", ":"))
            )

        self.assertEqual([], invariant_failures, "canonical-set permutation drift")
        self.assertEqual([], wrong_rejections, "mutations rejected by wrong surface")
        self.assertEqual(
            0,
            len(accepted),
            f"accepted mutations must be zero; accepted={accepted}",
        )


class TargetRosterFixRound1RedTests(unittest.TestCase):
    def test_valid_self_hash_is_not_scanned_as_raw_pnu(self) -> None:
        roster = make_roster()
        targets = list(roster["targets"])
        targets[10], targets[11] = targets[11], targets[10]
        roster["targets"] = tuple(targets)
        reseal(roster, "roster_sha256")
        self.assertRegex(roster["roster_sha256"], r"^[0-9a-f]{64}$")
        self.assertIsNotNone(
            re.search(r"(?<![0-9])[0-9]{19}(?![0-9])", roster["roster_sha256"])
        )

        with self.assertRaisesRegex(TargetRosterError, "target_order"):
            verify_target_roster(roster)

    def test_shared_source_missing_attack_reaches_source_closure(self) -> None:
        inputs = make_admission_inputs()
        replace_shared_target_source_with_missing(inputs)

        with self.assertRaisesRegex(
            TargetRosterError, "source_capture_reference_missing"
        ):
            verify_admission_inputs(**inputs)

    def test_rebalanced_cross_site_pairing_is_rejected(self) -> None:
        roster = make_roster()
        first = roster["targets"][0]
        second = roster["targets"][12]
        first["site_ref"], second["site_ref"] = second["site_ref"], first["site_ref"]

        with self.assertRaisesRegex(TargetRosterError, "target_site_pairing"):
            verify_target_roster(reseal(roster, "roster_sha256"))

    def test_resealed_evidence_family_source_swap_is_rejected(self) -> None:
        inputs = make_admission_inputs()
        spec = inputs["target_specs"][0]
        sources = spec["evidence_family_sources"]
        sources["geometry"], sources["law"] = sources["law"], sources["geometry"]
        spec["target_spec_sha256"] = oracle_record_sha256(spec, "target_spec_sha256")
        inputs["roster"]["targets"][0]["target_spec_sha256"] = spec[
            "target_spec_sha256"
        ]
        reseal(inputs["roster"], "roster_sha256")

        with self.assertRaisesRegex(
            TargetRosterError, "evidence_family_source_mapping"
        ):
            verify_admission_inputs(**inputs)

    def test_public_source_ids_reject_private_semantic_tokens(self) -> None:
        for token in ("geometry", "repeat-01", "alias-01"):
            roster = make_roster()
            roster["targets"][0]["source_ids"] = (token,)
            with self.subTest(token=token):
                with self.assertRaisesRegex(TargetRosterError, "protected_identifier"):
                    verify_target_roster(reseal(roster, "roster_sha256"))

    def test_omitted_source_object_has_stable_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_root = write_complete_inputs(root / "input")
            next((input_root / "source_objects").iterdir()).unlink()

            try:
                build_frozen_roster(input_root, root / "release")
            except TargetRosterError as exc:
                self.assertEqual(str(exc), "source_capture_missing_or_changed")
            except BaseException as exc:
                self.fail(
                    "omitted source escaped stable boundary: "
                    f"{type(exc).__name__}: {exc}"
                )
            else:
                self.fail("omitted source object was accepted")

    def test_nested_order_matrix_has_every_distinct_attack(self) -> None:
        expected_labels = {
            *(f"public-target:{index:02d}" for index in range(34)),
            *(
                f"target-spec:{index:02d}:{family}"
                for index in range(34)
                for family in ("geometry", "law", "parking", "program", "site")
            ),
            *(f"site-locator:{index:02d}" for index in range(3)),
        }
        observed_labels: set[str] = set()
        for index in range(34):
            roster = make_roster()
            source_ids = list(roster["targets"][index]["source_ids"])
            source_ids[0], source_ids[1] = source_ids[1], source_ids[0]
            roster["targets"][index]["source_ids"] = tuple(source_ids)
            with self.assertRaisesRegex(TargetRosterError, "source_ids"):
                verify_target_roster(reseal(roster, "roster_sha256"))
            observed_labels.add(f"public-target:{index:02d}")

        inputs = make_admission_inputs()
        for index, spec in enumerate(inputs["target_specs"]):
            for family in ("geometry", "law", "parking", "program", "site"):
                mutated = copy.deepcopy(spec)
                mutated["evidence_family_sources"][family] = tuple(
                    reversed(mutated["evidence_family_sources"][family])
                )
                with self.assertRaisesRegex(
                    TargetRosterError, "target_source_coverage_incomplete"
                ):
                    TargetSpecV1.from_dict(mutated)
                observed_labels.add(f"target-spec:{index:02d}:{family}")

        for index, locator in enumerate(inputs["locators"]):
            mutated = copy.deepcopy(locator)
            mutated["source_capture_ids"] = tuple(
                reversed(mutated["source_capture_ids"])
            )
            with self.assertRaisesRegex(
                TargetRosterError, "locator_source_capture_ids"
            ):
                SiteLocatorV1.from_dict(mutated)
            observed_labels.add(f"site-locator:{index:02d}")

        self.assertEqual(observed_labels, expected_labels)
