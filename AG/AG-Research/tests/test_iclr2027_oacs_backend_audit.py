"""Safety tests for the pre-generation backend audit."""

from __future__ import annotations

import ast
import io
import pathlib
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from iclr2027.oacs_backend_audit import (
    ApprovalTrustRootV1,
    BackendAuditConfigV1,
    QuotaAssumptionV1,
    UsageAccountingV1,
    approval_digest,
    audit_backend,
    parse_canonical_audit_bytes,
)


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


class RecordingProbe:
    """The only fake: it records the narrowly permitted external probe seam."""

    def __init__(self, *, version="1.2.3", auth="service_account", quota="declared"):
        self.calls = ()
        self.version_value = version
        self.auth_value = auth
        self.quota_value = quota

    def version(self):
        self.calls += ("version",)
        return self.version_value

    def auth_mode(self):
        self.calls += ("auth_mode",)
        return self.auth_value

    def quota_mode(self):
        self.calls += ("quota_mode",)
        return self.quota_value


class OacsBackendAuditTests(unittest.TestCase):
    def config(self, **changes):
        values = {
            "executable": "oacs-cli",
            "executable_sha256": HASH_A,
            "adapter": "oacs.adapter.v1",
            "adapter_sha256": HASH_B,
            "model_id": "provider/model-2026-09-01",
            "quota_assumptions": (
                QuotaAssumptionV1(
                    scope="requests_per_day", statement="100 requests per day"
                ),
            ),
            "invoice_approval_id": "APR-2026-09-02",
            "maximum_marginal_cost_microunits": 1_000_000,
            "timeout_seconds": 30,
            "retry_count": 1,
            "usage_accounting": UsageAccountingV1.all_accounted(),
            "evidence_provenance": "injected_metadata",
        }
        values.update(changes)
        return BackendAuditConfigV1(**values)

    def approval(self, **changes):
        values = {
            "executable_sha256": HASH_A,
            "runtime_version": "1.2.3",
            "adapter_sha256": HASH_B,
            "model_id": "provider/model-2026-09-01",
            "auth_mode": "service_account",
            "quota_mode": "declared",
            "quota_assumptions": self.config().quota_assumptions,
            "invoice_approval_id": "APR-2026-09-02",
            "maximum_marginal_cost_microunits": 1_000_000,
            "timeout_seconds": 30,
            "retry_count": 1,
            "usage_accounting": UsageAccountingV1.all_accounted(),
            "required_evidence_provenance": "injected_metadata",
        }
        values.update(changes)
        return ApprovalTrustRootV1(**values)

    def ready_audit(self, config=None, probe=None, approval=None, digest=None):
        approval = approval or self.approval()
        return audit_backend(
            config or self.config(),
            probe or RecordingProbe(),
            approval,
            digest or approval_digest(approval),
        )

    def test_forged_matching_config_and_evidence_are_not_ready_without_trust_anchor(
        self,
    ):
        forged = self.config(
            executable_sha256=HASH_C, adapter_sha256=HASH_C, model_id="provider/current"
        )
        audit = audit_backend(forged, RecordingProbe(version="9.9.9"))
        self.assertEqual(audit.status, "not_assessable")
        self.assertIn("approval_trust_root_unavailable", audit.reason_codes)
        forged_approval = self.approval(
            executable_sha256=HASH_C,
            runtime_version="9.9.9",
            adapter_sha256=HASH_C,
            model_id="provider/current",
        )
        audit = audit_backend(
            forged,
            RecordingProbe(version="9.9.9"),
            forged_approval,
            approval_digest(self.approval()),
        )
        self.assertEqual(audit.status, "not_assessable")
        self.assertIn("approval_trust_root_unavailable", audit.reason_codes)

    def test_unknown_auth_or_usage_is_not_ready(self):
        audit = self.ready_audit(probe=RecordingProbe(auth="unknown"))
        self.assertEqual(audit.status, "not_assessable")
        self.assertIn("auth_mode_mismatch", audit.reason_codes)

    def test_probe_calls_have_exact_metadata_only_surface(self):
        probe = RecordingProbe()
        self.ready_audit(probe=probe)
        self.assertEqual(probe.calls, ("version", "auth_mode", "quota_mode"))

    def test_audit_never_uses_generation_or_secret_probe_methods(self):
        class GuardedProbe(RecordingProbe):
            def generate(self):
                raise AssertionError("generation is forbidden in an audit")

            def credential_value(self):
                raise AssertionError("credential reads are forbidden in an audit")

        probe = GuardedProbe()
        self.ready_audit(probe=probe)
        self.assertEqual(probe.calls, ("version", "auth_mode", "quota_mode"))

    def test_secret_like_probe_values_are_not_serialized(self):
        audit = self.ready_audit(
            probe=RecordingProbe(auth="secret-value-not-for-audit")
        )
        self.assertEqual(audit.auth_mode, "unknown")
        self.assertNotIn(b"secret-value-not-for-audit", audit.canonical_bytes())
        audit = self.ready_audit(
            probe=RecordingProbe(version="secret-version-not-for-audit")
        )
        self.assertEqual(audit.runtime_version, "unknown")
        self.assertNotIn(b"secret-version-not-for-audit", audit.canonical_bytes())

    def test_ready_requires_trusted_approval_digest(self):
        audit = self.ready_audit()
        self.assertEqual(audit.status, "ready_for_separate_execution_review")
        self.assertEqual(audit.reason_codes, ())

    def test_missing_or_wrong_approval_digest_is_not_assessable(self):
        approval = self.approval()
        for digest in (None, HASH_C):
            audit = audit_backend(self.config(), RecordingProbe(), approval, digest)
            self.assertEqual(audit.status, "not_assessable")
            self.assertIn("approval_trust_root_unavailable", audit.reason_codes)

    def test_model_identity_matches_trusted_exact_model_not_an_alias_heuristic(self):
        audit = self.ready_audit(config=self.config(model_id="provider/current"))
        self.assertIn("model_identity_mismatch", audit.reason_codes)
        audit = self.ready_audit(
            config=self.config(model_id="provider/model-2026-09-01")
        )
        self.assertEqual(audit.status, "ready_for_separate_execution_review")

    def test_missing_and_blank_structured_quota_assumptions_reject(self):
        audit = self.ready_audit(config=self.config(quota_assumptions=()))
        self.assertIn("quota_assumptions_undeclared", audit.reason_codes)
        with self.assertRaises(ValueError):
            QuotaAssumptionV1(scope="requests_per_day", statement="  ")

    def test_missing_executable_is_not_assessable(self):
        audit = self.ready_audit(config=self.config(executable=""))
        self.assertIn("executable_unavailable", audit.reason_codes)

    def test_wrong_runtime_version_is_not_assessable(self):
        audit = self.ready_audit(probe=RecordingProbe(version="0.0.0"))
        self.assertIn("runtime_version_mismatch", audit.reason_codes)

    def test_unbounded_timeout_and_retry_are_not_assessable(self):
        audit = self.ready_audit(config=self.config(timeout_seconds=301, retry_count=6))
        self.assertIn("timeout_unbounded", audit.reason_codes)
        self.assertIn("retry_unbounded", audit.reason_codes)

    def test_omitted_selector_usage_accounting_is_not_assessable(self):
        accounting = UsageAccountingV1(True, False, True, True, True, True, True)
        audit = self.ready_audit(config=self.config(usage_accounting=accounting))
        self.assertIn("usage_accounting_incomplete", audit.reason_codes)

    def test_unverifiable_cache_and_failure_accounting_are_not_assessable(self):
        accounting = UsageAccountingV1(True, True, True, True, True, False, False)
        audit = self.ready_audit(config=self.config(usage_accounting=accounting))
        self.assertIn("cache_accounting_unverifiable", audit.reason_codes)
        self.assertIn("failure_accounting_incomplete", audit.reason_codes)

    def test_forged_zero_cost_metadata_is_not_assessable(self):
        audit = self.ready_audit(config=self.config(maximum_marginal_cost_microunits=0))
        self.assertIn("marginal_invoice_unapproved", audit.reason_codes)

    def test_invalid_hash_and_native_bool_integer_are_closed_schema_errors(self):
        with self.assertRaises(ValueError):
            self.config(executable_sha256="A" * 64)
        with self.assertRaises(TypeError):
            self.config(timeout_seconds=True)

    def test_canonical_parser_rejects_duplicate_and_noncanonical_json(self):
        audit = self.ready_audit()
        payload = audit.canonical_bytes()
        self.assertEqual(parse_canonical_audit_bytes(payload), audit)
        with self.assertRaises(ValueError):
            parse_canonical_audit_bytes(
                payload.replace(b'"status":', b'"status":"x","status":', 1)
            )
        with self.assertRaises(ValueError):
            parse_canonical_audit_bytes(payload[:-1] + b" \n")

    def test_no_opaque_executable_runner_surface_remains(self):
        import iclr2027.oacs_backend_audit as audit_module

        self.assertFalse(hasattr(audit_module, "LocalCommandMetadataProbe"))
        self.assertFalse(hasattr(audit_module, "LocalProbeCommandsV1"))

    def test_cli_forces_untrusted_approval_source(self):
        from audit_iclr2027_oacs_backend import main

        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            config_path = root / "config.json"
            evidence_path = root / "evidence.json"
            config_path.write_bytes(self.config().canonical_bytes())
            evidence_path.write_bytes(
                b'{"auth_mode":"service_account","quota_mode":"declared","version":"1.2.3"}\n'
            )
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = main(
                    [
                        "--config",
                        str(config_path),
                        "--probe-evidence",
                        str(evidence_path),
                    ]
                )
        self.assertEqual(code, 0, err.getvalue())
        cli_audit = parse_canonical_audit_bytes(out.getvalue().encode("utf-8"))
        self.assertEqual(cli_audit.status, "not_assessable")
        self.assertIn("approval_trust_root_unavailable", cli_audit.reason_codes)
        self.assertEqual(err.getvalue(), "")

    def test_real_cli_stdout_is_exact_canonical_bytes_with_one_lf(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            config_path = root / "config.json"
            evidence_path = root / "evidence.json"
            config_path.write_bytes(self.config().canonical_bytes())
            evidence_path.write_bytes(
                b'{"auth_mode":"service_account","quota_mode":"declared","version":"1.2.3"}\n'
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    "-E",
                    "-B",
                    "audit_iclr2027_oacs_backend.py",
                    "--config",
                    str(config_path),
                    "--probe-evidence",
                    str(evidence_path),
                ],
                cwd=pathlib.Path(__file__).parents[1],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        expected = audit_backend(self.config(), RecordingProbe()).canonical_bytes()
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, expected)
        self.assertTrue(completed.stdout.endswith(b"\n"))
        self.assertNotIn(b"\r\n", completed.stdout)
        self.assertEqual(completed.stderr, b"")

    def test_capability_scan_excludes_network_secret_generation_and_runner_imports(
        self,
    ):
        import iclr2027.oacs_backend_audit as audit_module

        tree = ast.parse(
            pathlib.Path(audit_module.__file__).read_text(encoding="utf-8")
        )
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports.update(
            node.module.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        )
        self.assertFalse(
            imports & {"os", "requests", "socket", "subprocess", "urllib", "openai"}
        )


if __name__ == "__main__":
    unittest.main()
