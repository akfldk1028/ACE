"""Static and isolated-process capability tests for receipt evaluators."""

from __future__ import annotations

import ast
import base64
import hashlib
import importlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from iclr2027.estimand_receipt_generator import generate_clean_benchmark


REPO = Path(__file__).resolve().parents[1]
EVALUATOR = REPO / "iclr2027" / "estimand_receipt_evaluators.py"
RECEIPTS = REPO / "iclr2027" / "estimand_receipts.py"
FORBIDDEN_IMPORT_PARTS = {
    "fault",
    "oracle",
    "test",
    "generator",
    "pathlib",
    "os",
    "glob",
    "subprocess",
    "multiprocessing",
    "socket",
    "urllib",
    "requests",
    "http",
    "importlib",
    "tempfile",
    "sys",
}
FORBIDDEN_CALLS = {
    "open",
    "exec",
    "eval",
    "compile",
    "system",
    "popen",
    "run",
    "call",
    "check_call",
    "check_output",
    "getcwd",
    "listdir",
    "scandir",
    "walk",
    "getenv",
    "__import__",
    "read",
    "read_text",
    "read_bytes",
}
FORBIDDEN_NAMES = {"__file__"}
FORBIDDEN_ATTRIBUTES = {"environ", "argv", "path", "stdin", "stdout", "stderr"}


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _imports(tree: ast.AST) -> tuple[str, ...]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.append(node.module or "")
    return tuple(names)


class EvaluatorCapabilityTests(unittest.TestCase):
    def test_receipt_and_evaluator_import_graphs_exclude_private_and_ambient_capabilities(
        self,
    ) -> None:
        # Catches direct imports of gold, faults, filesystem, environment, children, or network.
        self.assertTrue(EVALUATOR.is_file())
        for path in (RECEIPTS, EVALUATOR):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imports = _imports(tree)
            with self.subTest(path=path.name):
                for imported in imports:
                    lowered_parts = set(imported.lower().replace("-", "_").split("."))
                    self.assertTrue(
                        FORBIDDEN_IMPORT_PARTS.isdisjoint(lowered_parts),
                        imported,
                    )
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name):
                        self.assertNotIn(node.id, FORBIDDEN_NAMES)
                    if isinstance(node, ast.Attribute):
                        self.assertNotIn(node.attr, FORBIDDEN_ATTRIBUTES)
                    if not isinstance(node, ast.Call):
                        continue
                    called = None
                    if isinstance(node.func, ast.Name):
                        called = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        called = node.func.attr
                    self.assertNotIn(called, FORBIDDEN_CALLS)

    def test_evaluator_has_only_the_receipt_production_dependency(self) -> None:
        # Catches a transitive private-label dependency disguised as a local import.
        tree = ast.parse(EVALUATOR.read_text(encoding="utf-8"))
        local_imports = tuple(
            name for name in _imports(tree) if name.startswith("iclr2027")
        )
        self.assertEqual(local_imports, ("iclr2027.estimand_receipts",))

    def test_test_controller_can_run_evaluator_in_an_empty_isolated_process(
        self,
    ) -> None:
        # Catches evaluator dependence on cwd, environment, filename, or parent state.
        clean = generate_clean_benchmark()
        case_id = hashlib.sha256(b"isolated-case").hexdigest()
        trust = _canonical_bytes(clean.trust_root.to_dict())
        public = _canonical_bytes(
            {
                "schema_version": "public-artifact-row/v1",
                "case_id": case_id,
                "artifact": clean.artifacts[0].to_dict(),
            }
        )
        code = (
            "import base64,json,sys;"
            "sys.path.insert(0,sys.argv[1]);"
            "before=set(sys.modules);"
            "from iclr2027.estimand_receipt_evaluators import evaluate_frozen_artifacts;"
            "local=sorted(name for name in set(sys.modules)-before if name=='iclr2027' or name.startswith('iclr2027.'));"
            "request=json.loads(sys.stdin.buffer.read());"
            "rows=evaluate_frozen_artifacts((base64.b64decode(request['public']),),base64.b64decode(request['trust']));"
            "print(json.dumps({'count':len(rows),'local_graph':local,'statuses':[r.status for r in rows]},sort_keys=True,separators=(',',':')))"
        )
        request = json.dumps(
            {
                "public": base64.b64encode(public).decode("ascii"),
                "trust": base64.b64encode(trust).decode("ascii"),
            },
            separators=(",", ":"),
        )
        with tempfile.TemporaryDirectory() as temporary:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    "-S",
                    "-c",
                    code,
                    str(REPO),
                ],
                cwd=temporary,
                env={},
                check=False,
                capture_output=True,
                text=True,
                input=request,
                timeout=20,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        value = json.loads(completed.stdout)
        self.assertEqual(value["count"], 33)
        self.assertEqual(
            value["local_graph"],
            [
                "iclr2027",
                "iclr2027.estimand_receipt_evaluators",
                "iclr2027.estimand_receipts",
            ],
        )
        self.assertEqual(value["statuses"], ["CERTIFIED"] * 33)

    def test_historical_package_api_resolves_lazily(self) -> None:
        # Catches removal or recursion in the package-level compatibility API.
        package = importlib.import_module("iclr2027")
        resolved = package.resolve_exp01_summary
        audit = importlib.import_module("iclr2027.audit")
        self.assertIn("resolve_exp01_summary", package.__all__)
        self.assertIs(resolved, audit.resolve_exp01_summary)


if __name__ == "__main__":
    unittest.main()
