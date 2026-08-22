from __future__ import annotations

import json
from pathlib import Path

from django.test import SimpleTestCase


MEMORY_ROOT = (
    Path(__file__).resolve().parent
    / "maas"
    / "agents"
    / "maas_geometry_agent"
    / "memory"
)


class MaasGeometryMemoryContractTests(SimpleTestCase):
    def test_manifest_loads_every_required_memory_module_in_order(self):
        manifest = json.loads(
            (MEMORY_ROOT / "manifest.json").read_text(encoding="utf-8")
        )

        self.assertEqual(
            manifest["schema_version"],
            "arr.maas.geometry_agent_memory.v1",
        )
        modules = manifest["required_read_order"]
        self.assertEqual(
            modules,
            [
                "01_GOAL.md",
                "02_NON_NEGOTIABLES.md",
                "03_CAUSAL_PIPELINE.md",
                "04_BASEVOLUME_GRAPH.md",
                "05_BOOK_LANGUAGE.md",
                "06_LLM_HARNESS.md",
                "07_VALIDATION_GATES.md",
                "08_FAILURE_LEDGER.md",
                "09_CURRENT_STATE.md",
            ],
        )
        loaded = "\n".join(
            (MEMORY_ROOT / name).read_text(encoding="utf-8")
            for name in modules
        )
        self.assertIn(
            "UnitBox -> authored base-form capability -> one global 4x4 Matrix4",
            loaded,
        )
        self.assertIn("1/1, 3/8, 1/2, 1/4, 1/8, 1/16", loaded)
        self.assertIn("compiler-only preflight is not legal preflight", loaded)
        self.assertIn("capacity utilization >= 0.70", loaded)
        self.assertIn("deterministic morphology fallback is forbidden", loaded)

    def test_root_memory_is_a_small_mandatory_loader(self):
        root = (MEMORY_ROOT / "MEMORY.md").read_text(encoding="utf-8")

        self.assertIn("manifest.json", root)
        self.assertIn("required_read_order", root)
        self.assertLessEqual(len(root.splitlines()), 80)

