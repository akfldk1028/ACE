from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from dataclasses import fields, replace
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import build_iclr2027_oacs_preoutcome as build_cli
from build_iclr2027_oacs_preoutcome import main as build_main
from iclr2027.oacs_claim_ledger import verify_claim_ledger_bytes
from iclr2027.oacs_preflight import (
    evaluate_preflight,
    preflight_receipt_bytes,
)
from iclr2027.oacs_preflight_v2 import (
    OacsPreflightInputsV2,
    PreflightV2Error,
    UnavailableComponentV1,
    evaluate_preflight_v2,
    preflight_receipt_v2_bytes,
    unavailable_component_bytes,
    validate_preflight_receipt_v2_bytes,
    verify_preflight_receipt_v2_bytes,
    verify_unavailable_component_bytes,
)
from iclr2027.oacs_review_harness import (
    build_review_package,
    lock_review_record,
    locked_review_bytes,
    review_package_bytes,
)
import validate_iclr2027_oacs_preflight as validate_cli
from validate_iclr2027_oacs_preflight import main as validate_main
from tests.test_iclr2027_oacs_preflight import _SyntheticPreflight, _canonical


ARCHITECTURE_CODES = (
    "accepted_source_rights_absent",
    "blind_overlap_commitment_absent",
    "evaluator_commitment_absent",
    "no_admissible_units",
    "obligation_family_authority_absent",
    "partition_commitment_absent",
    "public_packet_commitment_absent",
    "source_manifest_commitment_absent",
    "unit_declarations_incomplete",
)
JCI_CODES = ("explicit_domain_declaration_absent", "no_admissible_units")
STUDY_CODES = (
    "budget_authority_absent",
    "capability_catalog_absent",
    "capability_crossover_absent",
    "common_synthesizer_absent",
    "e3_readiness_authority_absent",
    "model_binding_absent",
    "public_input_projection_absent",
    "retry_policy_absent",
    "terminal_evaluator_absent",
    "tool_catalog_authority_absent",
    "usage_accounting_absent",
)


def _envelope(
    component: str,
    codes: tuple[str, ...],
    *,
    upstream: str | None = None,
    supplied: tuple[str, ...] = (),
) -> bytes:
    census = component.endswith("_census")
    return unavailable_component_bytes(
        UnavailableComponentV1(
            schema="oacs-component-unavailable/v1",
            component=component,
            status="no_go_needs_context",
            missing_authority_codes=codes,
            admissible_unit_count=0 if census else None,
            upstream_component_sha256=upstream,
            supplied_authority_sha256=supplied,
        )
    )


class OacsPreflightV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = _SyntheticPreflight()

    @staticmethod
    def _convert(inputs, **changes: object) -> OacsPreflightInputsV2:
        values = {
            field.name: getattr(inputs, field.name)
            for field in fields(OacsPreflightInputsV2)
        }
        values.update(changes)
        return OacsPreflightInputsV2(**values)

    @staticmethod
    def _review_sources(inputs: OacsPreflightInputsV2) -> tuple[str, ...]:
        raw = (
            inputs.governing_design_bytes,
            inputs.architecture_census_bytes,
            inputs.jci_census_bytes,
            inputs.study_contract_bytes,
            inputs.backend_audit_bytes,
            inputs.architecture_power_plan_bytes,
            inputs.jci_power_plan_bytes,
        )
        hashes = {sha256(item).hexdigest() for item in raw}
        approval = inputs.approval_trust_root_bytes
        if approval is not None:
            hashes.add(sha256(approval).hexdigest())
        elif inputs.expected_approval_trust_root_sha256 is not None:
            hashes.add(inputs.expected_approval_trust_root_sha256)
        return tuple(sorted(hashes))

    def _relock(
        self,
        inputs: OacsPreflightInputsV2,
        *,
        sources: tuple[str, ...] | None = None,
    ) -> OacsPreflightInputsV2:
        ledger = verify_claim_ledger_bytes(inputs.claim_ledger_bytes)
        package = build_review_package(
            ledger,
            self._review_sources(inputs) if sources is None else sources,
        )
        reviews = tuple(
            locked_review_bytes(
                lock_review_record(
                    role=assignment.role,
                    assignment_sha256=assignment.assignment_sha256,
                    verdict="ACCEPT",
                    findings=(),
                )
            )
            for assignment in package.assignments
        )
        return replace(
            inputs,
            review_package_bytes=review_package_bytes(package),
            locked_review_bytes=reviews,
        )

    def _zero_domain_inputs(
        self,
        *,
        unavailable_study: bool = False,
    ) -> OacsPreflightInputsV2:
        positive = self.fixture.inputs()
        architecture = _envelope("architecture_census", ARCHITECTURE_CODES)
        jci = _envelope("jci_census", JCI_CODES)
        architecture_power = _envelope(
            "architecture_power_plan",
            ("upstream_census_unavailable",),
            upstream=sha256(architecture).hexdigest(),
        )
        jci_power = _envelope(
            "jci_power_plan",
            ("upstream_census_unavailable",),
            upstream=sha256(jci).hexdigest(),
        )
        study = (
            _envelope("study_contract", STUDY_CODES)
            if unavailable_study
            else positive.study_contract_bytes
        )
        return self._relock(
            self._convert(
                positive,
                architecture_census_bytes=architecture,
                jci_census_bytes=jci,
                architecture_power_plan_bytes=architecture_power,
                jci_power_plan_bytes=jci_power,
                study_contract_bytes=study,
            )
        )

    def test_unavailable_envelope_round_trip_is_exact_and_canonical(self) -> None:
        raw = _envelope(
            "architecture_census",
            ARCHITECTURE_CODES,
            supplied=("a" * 64, "b" * 64),
        )
        parsed = verify_unavailable_component_bytes(
            raw,
            expected_component="architecture_census",
        )
        self.assertEqual(unavailable_component_bytes(parsed), raw)
        self.assertTrue(raw.endswith(b"\n"))
        self.assertNotIn(b"\r", raw)

    def test_unavailable_envelope_rejects_every_structural_mutation(self) -> None:
        raw = _envelope("architecture_census", ARCHITECTURE_CODES)
        payload = json.loads(raw)
        attacks: list[tuple[str, bytes]] = []
        missing = dict(payload)
        missing.pop("status")
        attacks.append(("missing", _canonical(missing)))
        extra = {**payload, "extra": None}
        attacks.append(("extra", _canonical(extra)))
        attacks.append(("noncanonical", b" " + raw))
        wrong_status = {**payload, "status": "ready"}
        attacks.append(("status", _canonical(wrong_status)))
        empty_codes = {**payload, "missing_authority_codes": []}
        attacks.append(("empty-codes", _canonical(empty_codes)))
        duplicate_codes = {
            **payload,
            "missing_authority_codes": [*ARCHITECTURE_CODES, "no_admissible_units"],
        }
        attacks.append(("duplicate-codes", _canonical(duplicate_codes)))
        unknown_code = {**payload, "missing_authority_codes": ["unknown"]}
        attacks.append(("unknown-code", _canonical(unknown_code)))
        cross_code = {**payload, "missing_authority_codes": list(JCI_CODES)}
        attacks.append(("cross-code", _canonical(cross_code)))
        unsorted = {
            **payload,
            "missing_authority_codes": list(reversed(ARCHITECTURE_CODES)),
        }
        attacks.append(("unsorted", _canonical(unsorted)))
        duplicate_hash = {**payload, "supplied_authority_sha256": ["a" * 64] * 2}
        attacks.append(("duplicate-hash", _canonical(duplicate_hash)))
        unsorted_hashes = {
            **payload,
            "supplied_authority_sha256": ["b" * 64, "a" * 64],
        }
        attacks.append(("unsorted-hashes", _canonical(unsorted_hashes)))
        boolean_count = {**payload, "admissible_unit_count": False}
        attacks.append(("boolean-count", _canonical(boolean_count)))
        nonzero_count = {**payload, "admissible_unit_count": 1}
        attacks.append(("nonzero-count", _canonical(nonzero_count)))
        sentinel_hash = {**payload, "supplied_authority_sha256": ["missing"]}
        attacks.append(("sentinel-hash", _canonical(sentinel_hash)))
        attacks.append(
            (
                "negative-zero",
                raw.replace(
                    b'"admissible_unit_count":0', b'"admissible_unit_count":-0'
                ),
            )
        )
        attacks.append(
            (
                "nan",
                raw.replace(
                    b'"admissible_unit_count":0', b'"admissible_unit_count":NaN'
                ),
            )
        )
        attacks.append(
            (
                "infinity",
                raw.replace(
                    b'"admissible_unit_count":0',
                    b'"admissible_unit_count":Infinity',
                ),
            )
        )
        illegal_census_upstream = {
            **payload,
            "upstream_component_sha256": "a" * 64,
        }
        attacks.append(("census-upstream", _canonical(illegal_census_upstream)))
        study_payload = json.loads(_envelope("study_contract", STUDY_CODES))
        study_payload["upstream_component_sha256"] = "a" * 64
        attacks.append(("study-upstream", _canonical(study_payload)))
        wrong_study_codes = json.loads(_envelope("study_contract", STUDY_CODES))
        wrong_study_codes["missing_authority_codes"] = [
            "upstream_census_unavailable"
        ]
        attacks.append(("study-power-code", _canonical(wrong_study_codes)))
        duplicate_key = raw.replace(
            b'{"admissible_unit_count":',
            b'{"status":"no_go_needs_context","admissible_unit_count":',
            1,
        )
        attacks.append(("duplicate-key", duplicate_key))
        for label, attacked in attacks:
            with self.subTest(label=label):
                with self.assertRaises(PreflightV2Error):
                    verify_unavailable_component_bytes(attacked)

        with self.assertRaises(PreflightV2Error):
            verify_unavailable_component_bytes(
                raw,
                expected_component="jci_census",
            )
        with self.assertRaises(PreflightV2Error):
            _envelope(
                "architecture_power_plan",
                ("upstream_census_unavailable",),
                upstream=None,
            )

    def test_zero_censuses_and_bound_power_emit_typed_no_go(self) -> None:
        inputs = self._zero_domain_inputs()
        receipt = evaluate_preflight_v2(inputs)
        self.assertEqual(receipt.status, "no_go_needs_context")
        self.assertEqual(
            receipt.reason_codes,
            (
                "architecture_census_insufficient",
                "jci_census_insufficient",
                "prospective_power_insufficient",
            ),
        )
        self.assertEqual(len(receipt.unavailable_components), 4)
        for row in receipt.unavailable_components:
            slot = row["component"]
            raw = getattr(inputs, f"{slot}_bytes")
            self.assertEqual(row["component_sha256"], sha256(raw).hexdigest())
            self.assertEqual(receipt.component_sha256[slot], sha256(raw).hexdigest())
        raw = preflight_receipt_v2_bytes(receipt)
        self.assertEqual(verify_preflight_receipt_v2_bytes(raw), receipt)
        self.assertEqual(validate_preflight_receipt_v2_bytes(raw, inputs), raw)

    def test_one_positive_domain_and_one_unavailable_domain_do_not_pool(self) -> None:
        positive = self._convert(self.fixture.inputs())
        jci = _envelope("jci_census", JCI_CODES)
        jci_power = _envelope(
            "jci_power_plan",
            ("upstream_census_unavailable",),
            upstream=sha256(jci).hexdigest(),
        )
        inputs = self._relock(
            replace(
                positive,
                jci_census_bytes=jci,
                jci_power_plan_bytes=jci_power,
            )
        )
        receipt = evaluate_preflight_v2(inputs)
        self.assertEqual(
            receipt.reason_codes,
            ("jci_census_insufficient", "prospective_power_insufficient"),
        )
        self.assertEqual(
            tuple(row["component"] for row in receipt.unavailable_components),
            ("jci_census", "jci_power_plan"),
        )

    def test_census_power_pairs_are_slot_bound_and_cannot_mix_states(self) -> None:
        inputs = self._zero_domain_inputs()
        positive = self.fixture.inputs()
        cases = (
            replace(
                inputs,
                architecture_power_plan_bytes=(positive.architecture_power_plan_bytes),
            ),
            replace(
                inputs,
                architecture_power_plan_bytes=_envelope(
                    "architecture_power_plan",
                    ("upstream_census_unavailable",),
                    upstream=sha256(inputs.jci_census_bytes).hexdigest(),
                ),
            ),
            replace(
                inputs,
                architecture_power_plan_bytes=_envelope(
                    "jci_power_plan",
                    ("upstream_census_unavailable",),
                    upstream=sha256(inputs.architecture_census_bytes).hexdigest(),
                ),
            ),
        )
        for attacked in cases:
            with self.subTest():
                attacked = self._relock(attacked)
                with self.assertRaises(PreflightV2Error):
                    evaluate_preflight_v2(attacked)

    def test_review_package_requires_exact_negative_source_set(self) -> None:
        inputs = self._zero_domain_inputs()
        mutated_architecture = _envelope(
            "architecture_census",
            ARCHITECTURE_CODES,
            supplied=("a" * 64,),
        )
        stale = replace(inputs, architecture_census_bytes=mutated_architecture)
        with self.assertRaisesRegex(PreflightV2Error, "review package.*exact"):
            evaluate_preflight_v2(stale)

        exact = self._review_sources(inputs)
        for sources in (exact[:-1], tuple(sorted((*exact, "f" * 64)))):
            with self.subTest(source_count=len(sources)):
                attacked = self._relock(inputs, sources=sources)
                with self.assertRaisesRegex(PreflightV2Error, "review package.*exact"):
                    evaluate_preflight_v2(attacked)

    def test_typed_study_absence_has_exact_detail_without_treatments(self) -> None:
        inputs = self._zero_domain_inputs(unavailable_study=True)
        receipt = evaluate_preflight_v2(inputs)
        self.assertIn("study_parity_invalid", receipt.reason_codes)
        study = next(
            row
            for row in receipt.unavailable_components
            if row["component"] == "study_contract"
        )
        self.assertEqual(study["missing_authority_codes"], STUDY_CODES)
        self.assertNotIn(b"treatment_id", inputs.study_contract_bytes)

    def test_malformed_or_invalid_positive_bytes_never_become_unavailable(self) -> None:
        positive = self._convert(self.fixture.inputs())
        cases = (
            replace(positive, study_contract_bytes=b"{}\n"),
            replace(positive, study_contract_bytes=b"not-json\n"),
            replace(
                positive,
                study_contract_bytes=self.fixture._study_bytes(parity_valid=False),
            ),
            replace(positive, architecture_census_bytes=b"{}\n"),
            replace(positive, architecture_power_plan_bytes=b"{}\n"),
        )
        for inputs in cases:
            with self.subTest():
                with self.assertRaises(PreflightV2Error):
                    evaluate_preflight_v2(inputs)

    def test_receipt_unavailability_mutations_fail_even_when_resealed(self) -> None:
        inputs = self._zero_domain_inputs()
        raw = preflight_receipt_v2_bytes(evaluate_preflight_v2(inputs))
        attacks = []
        deleted = json.loads(raw)
        deleted["unavailable_components"].pop()
        attacks.append(deleted)
        reordered = json.loads(raw)
        reordered["unavailable_components"].reverse()
        attacks.append(reordered)
        wrong_hash = json.loads(raw)
        wrong_hash["unavailable_components"][0]["component_sha256"] = "f" * 64
        attacks.append(wrong_hash)
        reason_deleted = json.loads(raw)
        reason_deleted["reason_codes"].remove("prospective_power_insufficient")
        attacks.append(reason_deleted)
        for attacked in attacks:
            body = dict(attacked)
            body.pop("receipt_sha256")
            attacked["receipt_sha256"] = sha256(_canonical(body)).hexdigest()
            with self.subTest():
                attacked_raw = _canonical(attacked)
                with self.assertRaises(PreflightV2Error):
                    validate_preflight_receipt_v2_bytes(attacked_raw, inputs)

        self_hash = json.loads(raw)
        self_hash["receipt_sha256"] = "0" * 64
        with self.assertRaisesRegex(PreflightV2Error, "self-hash"):
            verify_preflight_receipt_v2_bytes(_canonical(self_hash))

    def test_all_positive_v2_delegates_to_exact_v1_gates(self) -> None:
        v1_inputs = self.fixture.inputs()
        v1_raw = preflight_receipt_bytes(evaluate_preflight(v1_inputs))
        self.assertEqual(len(v1_raw), 2318)
        self.assertEqual(
            sha256(v1_raw).hexdigest(),
            "a1b39b0952b48c489268a8cbde62d8139b84bc66e9301de46d107650069cc372",
        )
        v1_receipt = evaluate_preflight(v1_inputs)
        v2_receipt = evaluate_preflight_v2(self._convert(v1_inputs))
        self.assertEqual(v2_receipt.status, v1_receipt.status)
        self.assertEqual(v2_receipt.reason_codes, v1_receipt.reason_codes)
        self.assertEqual(
            dict(v2_receipt.component_sha256), dict(v1_receipt.component_sha256)
        )
        self.assertEqual(v2_receipt.unavailable_components, ())


class OacsPreflightV2CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case = OacsPreflightV2Tests(methodName="runTest")
        self.case.setUp()
        self.inputs = self.case._zero_domain_inputs(unavailable_study=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="oacs-preflight-v2-")
        self.root = Path(self.temporary.name).resolve(strict=True)
        self.paths = self._write_inputs()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_inputs(self) -> dict[str, Path]:
        rows = {
            "governing-design.md": self.inputs.governing_design_bytes,
            "claim-ledger.json": self.inputs.claim_ledger_bytes,
            "review-package.json": self.inputs.review_package_bytes,
            "architecture-census.json": self.inputs.architecture_census_bytes,
            "jci-census.json": self.inputs.jci_census_bytes,
            "study-contract.json": self.inputs.study_contract_bytes,
            "backend-audit.json": self.inputs.backend_audit_bytes,
            "architecture-power-plan.json": self.inputs.architecture_power_plan_bytes,
            "jci-power-plan.json": self.inputs.jci_power_plan_bytes,
            "approval-trust-root.json": self.inputs.approval_trust_root_bytes,
        }
        rows.update(
            {
                f"review-{role}.json": raw
                for role, raw in zip(
                    (
                        "problem-novelty",
                        "causal-statistics",
                        "experiment-reproducibility",
                        "adversarial-falsifier",
                    ),
                    self.inputs.locked_review_bytes,
                    strict=True,
                )
            }
        )
        paths = {}
        for name, raw in rows.items():
            self.assertIsInstance(raw, bytes)
            path = self.root / name
            path.write_bytes(raw)
            paths[name] = path
        return paths

    def _build_args(self, output: Path, *, version: bool = True) -> list[str]:
        args = [
            "--governing-design",
            str(self.paths["governing-design.md"]),
            "--governing-design-sha256",
            self.inputs.expected_governing_design_sha256,
            "--claim-ledger",
            str(self.paths["claim-ledger.json"]),
            "--review-package",
            str(self.paths["review-package.json"]),
            "--review-problem-novelty",
            str(self.paths["review-problem-novelty.json"]),
            "--review-causal-statistics",
            str(self.paths["review-causal-statistics.json"]),
            "--review-experiment-reproducibility",
            str(self.paths["review-experiment-reproducibility.json"]),
            "--review-adversarial-falsifier",
            str(self.paths["review-adversarial-falsifier.json"]),
            "--architecture-census",
            str(self.paths["architecture-census.json"]),
            "--jci-census",
            str(self.paths["jci-census.json"]),
            "--study-contract",
            str(self.paths["study-contract.json"]),
            "--backend-audit",
            str(self.paths["backend-audit.json"]),
            "--approval-trust-root",
            str(self.paths["approval-trust-root.json"]),
            "--approval-trust-root-sha256",
            self.inputs.expected_approval_trust_root_sha256,
            "--architecture-power-plan",
            str(self.paths["architecture-power-plan.json"]),
            "--jci-power-plan",
            str(self.paths["jci-power-plan.json"]),
            "--output-root",
            str(output),
        ]
        return ["--preflight-version", "v2", *args] if version else args

    def _validate_args(self, output: Path, *, version: bool = True) -> list[str]:
        args = [
            "--input-root",
            str(output),
            "--governing-design-sha256",
            self.inputs.expected_governing_design_sha256,
            "--approval-trust-root-sha256",
            self.inputs.expected_approval_trust_root_sha256,
        ]
        return ["--preflight-version", "v2", *args] if version else args

    @staticmethod
    def _run(function, args: list[str]) -> tuple[int, bytes, str]:
        binary = io.BytesIO()

        class _Stdout:
            buffer = binary

            @staticmethod
            def write(value: str) -> int:
                return len(value)

            @staticmethod
            def flush() -> None:
                return None

        errors = io.StringIO()
        with redirect_stdout(_Stdout()), redirect_stderr(errors):
            code = function(args)
        return code, binary.getvalue(), errors.getvalue()

    def test_explicit_v2_builder_and_validator_are_deterministic(self) -> None:
        outputs = (self.root / "package-a-final", self.root / "package-b-final")
        built = tuple(self._run(build_main, self._build_args(root)) for root in outputs)
        for code, stdout, errors in built:
            self.assertEqual((code, errors), (0, ""))
            self.assertEqual(
                verify_preflight_receipt_v2_bytes(stdout).status, "no_go_needs_context"
            )
            self.assertTrue(
                all(
                    value == 0
                    for value in json.loads(stdout)["operation_counters"].values()
                )
            )
        self.assertEqual(built[0][1], built[1][1])
        validated = tuple(
            self._run(validate_main, self._validate_args(root)) for root in outputs
        )
        for code, stdout, errors in validated:
            self.assertEqual((code, errors), (0, ""))
            self.assertEqual(stdout, built[0][1])

    def test_default_remains_v1_and_never_auto_detects_v2(self) -> None:
        output = self.root / "default-v1-final"
        code, stdout, errors = self._run(
            build_main,
            self._build_args(output, version=False),
        )
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, b"")
        self.assertFalse(os.path.lexists(output))
        self.assertIn("canonical and valid", errors)

        self.assertEqual(build_cli._parser().get_default("preflight_version"), "v1")
        self.assertEqual(validate_cli._parser().get_default("preflight_version"), "v1")

    def test_v2_subprocess_stdout_is_binary_canonical(self) -> None:
        project = Path(__file__).resolve(strict=True).parents[1]
        output = self.root / "subprocess-final"
        built = subprocess.run(
            [
                sys.executable,
                "-E",
                "-B",
                str(project / "build_iclr2027_oacs_preoutcome.py"),
                *self._build_args(output),
            ],
            check=False,
            capture_output=True,
        )
        self.assertEqual((built.returncode, built.stderr), (0, b""))
        self.assertTrue(built.stdout.endswith(b"\n"))
        self.assertNotIn(b"\r", built.stdout)
        validated = subprocess.run(
            [
                sys.executable,
                "-E",
                "-B",
                str(project / "validate_iclr2027_oacs_preflight.py"),
                *self._validate_args(output),
            ],
            check=False,
            capture_output=True,
        )
        self.assertEqual((validated.returncode, validated.stderr), (0, b""))
        self.assertEqual(validated.stdout, built.stdout)


if __name__ == "__main__":
    unittest.main()
