from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

from django.test import SimpleTestCase


ARR_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = (
    ARR_ROOT
    / ".superpowers"
    / "sdd"
    / "2026-08-05-llm-authored-diverse-legal-mass"
)
C53_BUNDLE = EVIDENCE_ROOT / "tmp-v31-c53-b01"


def _load_static_validator():
    sys.path.insert(0, str(EVIDENCE_ROOT))
    path = EVIDENCE_ROOT / "validate_static_codex_mass_v11.py"
    spec = importlib.util.spec_from_file_location("maas_static_v11_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load static validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MaasStaticPreflightContractTests(SimpleTestCase):
    def test_c68_direct_fit_null_is_deferred_to_continuous_production_gate(self):
        validator = _load_static_validator()

        result = validator.validate_static_package(
            C53_BUNDLE / "c68-full-height-notch-fragment-v1",
            C53_BUNDLE / "codex-mass-manifest-c68-full-height-notch-v1.json",
            C53_BUNDLE
            / "codex-mass-manifest-c68-full-height-notch-v1-admission.json",
            maximum_programs=1,
        )

        self.assertTrue(result["static_authorship"]["hard_pass"])
        self.assertTrue(result["hard_pass"])
        self.assertEqual(
            result["preflight"]["continuous_projection_required_count"],
            1,
        )
        self.assertEqual(result["preflight"]["failure_count"], 0)
        self.assertEqual(
            result["preflight"]["deferred"][0]["reason"],
            "continuous_legal_envelope_production_gate_required",
        )

    def test_preflight_does_not_require_scopes_absent_from_exact_llm_offer(self):
        validator = _load_static_validator()

        result = validator.validate_static_package(
            C53_BUNDLE / "c78-v8-pilot5-r1-authored-fragments",
            C53_BUNDLE / "codex-mass-manifest-c78-v8-pilot5-r1.json",
            C53_BUNDLE
            / "codex-mass-manifest-c78-v8-pilot5-r1-admission.json",
            maximum_programs=5,
        )

        self.assertTrue(result["hard_pass"])
        self.assertEqual(result["preflight"]["required_scope_count"], 1)
        self.assertEqual(
            result["preflight"]["continuous_projection_required_count"],
            5,
        )
