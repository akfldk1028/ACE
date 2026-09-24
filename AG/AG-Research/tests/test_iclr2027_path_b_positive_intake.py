from __future__ import annotations

import ast
from collections import Counter
from dataclasses import FrozenInstanceError, replace
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "iclr2027" / "path_b_positive_intake.py"
CLI_PATH = ROOT / "validate_iclr2027_path_b_positive_intake.py"

EXPECTED_REASON_CODES = (
    "approval_authentication_failed",
    "canonical_file_encoding_failed",
    "core_record_census_mismatch",
    "cryptographic_signature_failed",
    "external_root_missing",
    "filesystem_identity_failed",
    "immutable_member_census_mismatch",
    "locator_authentication_failed",
    "package_index_binding_failed",
    "process_spec_custody_failed",
    "producer_reviewer_authority_overlap",
    "replay_or_freshness_failed",
    "scientific_contract_drift",
    "task5_parent_custody_failed",
    "verifier_package_or_rotation_failed",
)
EXPECTED_COUNTER_FIELDS = (
    "external_artifact_count",
    "external_signature_count",
    "external_review_count",
    "authenticated_locator_count",
    "authenticated_package_count",
    "task6_vnext_authority_count",
    "task6_vnext_implementation_count",
    "candidate_path_construction_count",
    "locator_open_count",
    "candidate_root_open_count",
    "package_index_read_count",
    "member_read_count",
    "source_read_count",
    "data_read_count",
    "result_read_count",
    "rate_read_count",
    "simulation_draw_count",
    "model_call_count",
    "tool_call_count",
    "paid_call_count",
    "output_write_count",
    "operation_count",
    "automatic_retry_count",
    "fallback_count",
)
EXPECTED_BOOLEAN_FIELDS = (
    "task6_vnext_commission_eligible",
    "source_access_authorized",
    "simulation_authorized",
    "paid_run_authorized",
    "official_result_eligible",
)
EXPECTED_HELP_BYTES = (
    b"usage: validate_iclr2027_path_b_positive_intake.py [-h] (--current-status |\n"
    b"                                                   --list-negative-fixtures)\n"
    b"\n"
    b"Report Generation-0 Path-B positive-intake no-go status.\n"
    b"\n"
    b"options:\n"
    b"  -h, --help            show this help message and exit\n"
    b"  --current-status\n"
    b"  --list-negative-fixtures\n"
)
EXPECTED_ARGUMENT_ERROR_BYTES = b"error: invalid arguments\n"


def _module():
    try:
        return importlib.import_module("iclr2027.path_b_positive_intake")
    except ModuleNotFoundError as error:
        raise AssertionError("positive-intake orchestrator module is absent") from error


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


class _HostileCapability:
    def __init__(self) -> None:
        object.__setattr__(self, "observation_count", 0)

    def _trip(self, protocol: str) -> object:
        count = object.__getattribute__(self, "observation_count")
        object.__setattr__(self, "observation_count", count + 1)
        raise AssertionError(f"capability protocol observed: {protocol}")

    def __getattribute__(self, name: str) -> object:
        if name in {"observation_count", "_trip"}:
            return object.__getattribute__(self, name)
        return object.__getattribute__(self, "_trip")(f"attribute:{name}")

    def __iter__(self) -> object:
        return object.__getattribute__(self, "_trip")("iteration")

    def __getitem__(self, key: object) -> object:
        del key
        return object.__getattribute__(self, "_trip")("mapping")

    def __contains__(self, value: object) -> object:
        del value
        return object.__getattribute__(self, "_trip")("containment")

    def __len__(self) -> object:
        return object.__getattribute__(self, "_trip")("length")

    def __fspath__(self) -> object:
        return object.__getattribute__(self, "_trip")("path")

    def __str__(self) -> object:
        return object.__getattribute__(self, "_trip")("string")

    def __bool__(self) -> object:
        return object.__getattribute__(self, "_trip")("boolean")

    def __hash__(self) -> object:
        return object.__getattribute__(self, "_trip")("hash")

    def __repr__(self) -> object:
        return object.__getattribute__(self, "_trip")("representation")


class _TaskSevenHostileCapability(_HostileCapability):
    def __bytes__(self) -> object:
        return object.__getattribute__(self, "_trip")("bytes")

    def __eq__(self, other: object) -> object:
        del other
        return object.__getattribute__(self, "_trip")("equality")

    def __ne__(self, other: object) -> object:
        del other
        return object.__getattribute__(self, "_trip")("inequality")

    def __enter__(self) -> object:
        return object.__getattribute__(self, "_trip")("context-enter")

    def __exit__(self, *arguments: object) -> object:
        del arguments
        return object.__getattribute__(self, "_trip")("context-exit")

    def __aenter__(self) -> object:
        return object.__getattribute__(self, "_trip")("async-context-enter")

    def __aexit__(self, *arguments: object) -> object:
        del arguments
        return object.__getattribute__(self, "_trip")("async-context-exit")

    def __await__(self) -> object:
        return object.__getattribute__(self, "_trip")("await")

    def __copy__(self) -> object:
        return object.__getattribute__(self, "_trip")("copy")

    def __deepcopy__(self, memo: object) -> object:
        del memo
        return object.__getattribute__(self, "_trip")("deepcopy")

    def __reduce__(self) -> object:
        return object.__getattribute__(self, "_trip")("reduce")

    def __reduce_ex__(self, protocol: object) -> object:
        del protocol
        return object.__getattribute__(self, "_trip")("reduce-ex")

    def __getstate__(self) -> object:
        return object.__getattribute__(self, "_trip")("getstate")

    def __setstate__(self, state: object) -> object:
        del state
        return object.__getattribute__(self, "_trip")("setstate")


def _authenticated_entrypoint_is_exact(source: str) -> bool:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    functions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "validate_authenticated_path_b_intake"
    ]
    if len(functions) != 1 or isinstance(functions[0], ast.AsyncFunctionDef):
        return False
    function = functions[0]
    positional = (*function.args.posonlyargs, *function.args.args)
    if (
        tuple(argument.arg for argument in positional) != ("capability",)
        or function.args.vararg is not None
        or function.args.kwarg is not None
        or function.args.kwonlyargs
        or function.decorator_list
    ):
        return False
    body = function.body
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]
    if len(body) != 2:
        return False
    delete, raised = body
    if not (
        isinstance(delete, ast.Delete)
        and len(delete.targets) == 1
        and isinstance(delete.targets[0], ast.Name)
        and delete.targets[0].id == "capability"
    ):
        return False
    if not (
        isinstance(raised, ast.Raise)
        and raised.cause is None
        and isinstance(raised.exc, ast.Call)
        and isinstance(raised.exc.func, ast.Name)
        and raised.exc.func.id == "NeedsContextError"
        and len(raised.exc.args) == 1
        and isinstance(raised.exc.args[0], ast.Constant)
        and raised.exc.args[0].value == "external_root_missing"
        and not raised.exc.keywords
    ):
        return False
    return True


_PRODUCTION_IMPORTS = (
    ("from", "__future__", (("annotations", None),), 0),
    ("from", "dataclasses", (("dataclass", None),), 0),
    ("import", (("json", None),)),
    ("from", "typing", (("NoReturn", None),), 0),
    (
        "from",
        "iclr2027.path_b_positive_intake_contract",
        (("IntakeContractError", None),),
        0,
    ),
    (
        "from",
        "iclr2027.path_b_positive_intake_crypto",
        (("IntakeCryptoError", None),),
        0,
    ),
    (
        "from",
        "iclr2027.path_b_positive_intake_science",
        (
            ("SyntheticPackageView", None),
            ("validate_frozen_scientific_contract", None),
            ("validate_global_role_separation", None),
        ),
        0,
    ),
)
_CLI_IMPORTS = (
    ("from", "__future__", (("annotations", None),), 0),
    ("import", (("argparse", None),)),
    ("import", (("json", None),)),
    ("import", (("sys", None),)),
    (
        "from",
        "iclr2027",
        (("path_b_positive_intake", "intake"),),
        0,
    ),
)
_PRODUCTION_CALLS = {
    "NeedsContextError",
    "_GenerationZeroStatus",
    "_NegativeFixture",
    "_canonical_json",
    "dataclass",
    "json.dumps",
    "list",
    "self.to_dict",
    "tuple",
    "validate_frozen_scientific_contract",
    "validate_global_role_separation",
}
_CLI_CALLS = {
    "SystemExit",
    "_ClosedArgumentParser",
    "_canonical_json",
    "_parser",
    "argparse.HelpFormatter",
    "group.add_argument",
    "intake.current_status",
    "intake.current_status().to_json",
    "intake.negative_fixture_registry",
    "item.to_dict",
    "json.dumps",
    "main",
    "output.encode",
    "parser.add_mutually_exclusive_group",
    "parser.error",
    "parser.parse_args",
    "sys.stderr.buffer.write",
    "sys.stderr.reconfigure",
    "sys.stdout.buffer.write",
    "sys.stdout.reconfigure",
}
_PRODUCTION_PUBLIC_FUNCTIONS = (
    "current_status",
    "negative_fixture_registry",
    "validate_synthetic_path_b_contract",
    "validate_authenticated_path_b_intake",
)
_PRODUCTION_PUBLIC_CLASSES = ("NeedsContextError",)
_PRODUCTION_EXPORTS = (
    "IntakeContractError",
    "NeedsContextError",
    "current_status",
    "negative_fixture_registry",
    "validate_synthetic_path_b_contract",
    "validate_authenticated_path_b_intake",
)
_PRODUCTION_TOP_LEVEL_ASSIGNMENTS = (
    "__all__",
    "_REASON_CODES",
    "_FIXTURES",
    "_CURRENT_STATUS",
)
_CLI_TOP_LEVEL_ASSIGNMENTS = ("_ARGUMENT_ERROR",)
_PRODUCTION_MODULE_ATTRIBUTES = {"json": {"dumps"}}
_CLI_MODULE_ATTRIBUTES = {
    "argparse": {"ArgumentParser", "HelpFormatter"},
    "intake": {"current_status", "negative_fixture_registry"},
    "json": {"dumps"},
    "sys": {"argv", "stderr", "stdout"},
}


def _observed_imports(tree: ast.Module) -> tuple[object, ...]:
    imports: list[object] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.append(
                ("import", tuple((alias.name, alias.asname) for alias in node.names))
            )
        elif isinstance(node, ast.ImportFrom):
            imports.append(
                (
                    "from",
                    node.module,
                    tuple((alias.name, alias.asname) for alias in node.names),
                    node.level,
                )
            )
    return tuple(imports)


def _observed_top_level_assignments(tree: ast.Module) -> tuple[str, ...]:
    return tuple(
        target.id
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (node.targets if isinstance(node, ast.Assign) else (node.target,))
        if isinstance(target, ast.Name)
    )


def _cli_sinks_are_exact(tree: ast.Module) -> bool:
    expected = Counter(
        ast.dump(ast.parse(expression, mode="eval").body)
        for expression in (
            "sys.stderr.buffer.write(_ARGUMENT_ERROR)",
            'sys.stdout.reconfigure(encoding="utf-8", errors="strict", newline="\\n")',
            'sys.stderr.reconfigure(encoding="utf-8", errors="strict", newline="\\n")',
            'sys.stdout.buffer.write(output.encode("ascii") + b"\\n")',
        )
    )
    observed = Counter(
        ast.dump(node)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and ast.unparse(node.func).startswith(("sys.stdout", "sys.stderr"))
    )
    return observed == expected


def _capability_policy_violations(source: str, *, cli: bool = False) -> tuple[str, ...]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ("syntax-error",)
    violations: list[str] = []
    expected_imports = _CLI_IMPORTS if cli else _PRODUCTION_IMPORTS
    if _observed_imports(tree) != expected_imports:
        violations.append("import-allowlist-drift")
    expected_assignments = (
        _CLI_TOP_LEVEL_ASSIGNMENTS if cli else _PRODUCTION_TOP_LEVEL_ASSIGNMENTS
    )
    if _observed_top_level_assignments(tree) != expected_assignments:
        violations.append("module-assignment-drift")

    allowed_calls = _CLI_CALLS if cli else _PRODUCTION_CALLS
    allowed_module_attributes = (
        _CLI_MODULE_ATTRIBUTES if cli else _PRODUCTION_MODULE_ATTRIBUTES
    )
    trusted_names = (
        {"argparse", "intake", "json", "main", "sys"}
        if cli
        else {
            "IntakeContractError",
            "NeedsContextError",
            "SyntheticPackageView",
            "current_status",
            "dataclass",
            "json",
            "negative_fixture_registry",
            "validate_authenticated_path_b_intake",
            "validate_frozen_scientific_contract",
            "validate_global_role_separation",
            "validate_synthetic_path_b_contract",
        }
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            operation = ast.unparse(node.func)
            if operation not in allowed_calls:
                violations.append(f"operation-not-allowed:{operation}")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            violations.append(f"dunder-attribute-not-allowed:{node.attr}")
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id in allowed_module_attributes
            and node.attr not in allowed_module_attributes[node.value.id]
        ):
            violations.append(
                f"module-attribute-not-allowed:{node.value.id}.{node.attr}"
            )
        if (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Store)
            and node.id in trusted_names
        ):
            violations.append(f"trusted-name-rebound:{node.id}")
        if isinstance(node, ast.arg) and node.arg in trusted_names:
            violations.append(f"trusted-name-shadowed:{node.arg}")

    public_functions = tuple(
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    )
    public_classes = tuple(
        node.name
        for node in tree.body
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_")
    )
    if cli:
        if public_functions != ("main",) or public_classes:
            violations.append("cli-public-operation-drift")
        if not _cli_sinks_are_exact(tree):
            violations.append("cli-sink-drift")
    else:
        if public_functions != _PRODUCTION_PUBLIC_FUNCTIONS:
            violations.append("production-public-operation-drift")
        if public_classes != _PRODUCTION_PUBLIC_CLASSES:
            violations.append("production-public-class-drift")
        exports = [
            node
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "__all__"
                for target in node.targets
            )
        ]
        if (
            len(exports) != 1
            or ast.literal_eval(exports[0].value) != _PRODUCTION_EXPORTS
        ):
            violations.append("production-export-drift")
        if not _authenticated_entrypoint_is_exact(source):
            violations.append("authenticated-entrypoint-not-exact")
    return tuple(violations)


class GenerationZeroApiTests(unittest.TestCase):
    def test_current_status_is_exact_immutable_no_go_with_zero_authority(self) -> None:
        module = _module()
        first = module.current_status()
        second = module.current_status()
        self.assertEqual(first, second)
        self.assertFalse(hasattr(first, "__dict__"))
        with self.assertRaises((AttributeError, FrozenInstanceError)):
            first.status = "pass"
        expected = {
            "schema_version": "ace.iclr2027.path_b_positive_intake_generation0_status.v1",
            "authority_mode": "external_bootstrap_absent",
            "status": "no_go",
            "reason_codes": ["external_root_missing"],
            "empirical_status": "no_go_needs_context",
            "synthetic_only": True,
            **{name: 0 for name in EXPECTED_COUNTER_FIELDS},
            **{name: False for name in EXPECTED_BOOLEAN_FIELDS},
        }
        self.assertEqual(first.to_dict(), expected)
        self.assertEqual(first.to_json(), _canonical(expected))
        self.assertNotIn("capability", first.to_dict())
        self.assertNotIn("authority_receipt", first.to_dict())

    def test_negative_fixture_registry_closes_each_design_reason_family(self) -> None:
        module = _module()
        registry = module.negative_fixture_registry()
        self.assertIsInstance(registry, tuple)
        self.assertEqual(
            tuple(item.reason_code for item in registry), EXPECTED_REASON_CODES
        )
        self.assertEqual(
            tuple(item.fixture_id for item in registry), EXPECTED_REASON_CODES
        )
        self.assertEqual(
            tuple(item.reason_code for item in registry),
            tuple(sorted(EXPECTED_REASON_CODES, key=lambda item: item.encode("ascii"))),
        )
        for item in registry:
            self.assertFalse(hasattr(item, "__dict__"))
            self.assertEqual(
                item.to_dict(),
                {
                    "schema_version": "ace.iclr2027.path_b_positive_intake_negative_fixture.v1",
                    "fixture_id": item.fixture_id,
                    "reason_code": item.reason_code,
                    "required_outcome": "reject_without_authority",
                },
            )

    def test_authenticated_intake_rejects_without_observing_any_protocol(self) -> None:
        module = _module()
        hostile = _HostileCapability()
        with self.assertRaisesRegex(
            module.NeedsContextError, "^external_root_missing$"
        ):
            module.validate_authenticated_path_b_intake(hostile)
        self.assertEqual(hostile.observation_count, 0)

    def test_synthetic_validation_checks_real_science_and_returns_no_authority(
        self,
    ) -> None:
        module = _module()
        science_test = importlib.import_module(
            "tests.test_iclr2027_path_b_positive_intake_science"
        )
        package = science_test._package()
        self.assertIsNone(module.validate_synthetic_path_b_contract(package))
        changed_science = replace(package.scientific_contract, legacy_continuity=True)
        changed = replace(package, scientific_contract=changed_science)
        with self.assertRaisesRegex(
            module.IntakeContractError, "legacy_continuity_drift"
        ):
            module.validate_synthetic_path_b_contract(changed)


class GenerationZeroCliTests(unittest.TestCase):
    def _run(
        self,
        *arguments: str,
        environment: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[bytes]:
        process_environment = dict(os.environ)
        if environment is not None:
            process_environment.update(environment)
        return subprocess.run(
            [sys.executable, "-B", str(CLI_PATH), *arguments],
            cwd=ROOT,
            shell=False,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=False,
            check=False,
            env=process_environment,
        )

    def test_current_status_raw_cli_is_byte_deterministic_lf_only(self) -> None:
        module = _module()
        first = self._run("--current-status")
        second = self._run("--current-status")
        self.assertEqual(first.returncode, 0)
        self.assertEqual(first.stderr, b"")
        self.assertEqual(first.stdout, second.stdout)
        self.assertTrue(first.stdout.endswith(b"\n"))
        self.assertNotIn(b"\r", first.stdout)
        self.assertFalse(first.stdout.endswith(b"\n\n"))
        self.assertEqual(
            first.stdout,
            (module.current_status().to_json() + "\n").encode("ascii"),
        )

    def test_negative_fixture_raw_cli_is_canonical_and_lf_only(self) -> None:
        module = _module()
        first = self._run("--list-negative-fixtures")
        second = self._run("--list-negative-fixtures")
        expected = [item.to_dict() for item in module.negative_fixture_registry()]
        self.assertEqual(first.returncode, 0)
        self.assertEqual(first.stderr, b"")
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(first.stdout, (_canonical(expected) + "\n").encode("ascii"))
        self.assertNotIn(b"\r", first.stdout)

    def test_help_is_the_only_other_successful_cli_surface(self) -> None:
        completed = self._run("--help")
        repeated = self._run("--help")
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stderr, b"")
        self.assertEqual(completed.stdout, repeated.stdout)
        self.assertTrue(completed.stdout.endswith(b"\n"))
        self.assertNotIn(b"\r", completed.stdout)
        self.assertIn(b"--current-status", completed.stdout)
        self.assertIn(b"--list-negative-fixtures", completed.stdout)
        for forbidden in (
            b"--path",
            b"--key",
            b"--root",
            b"--signature",
            b"--source",
            b"--data",
            b"--rate",
            b"--output",
        ):
            self.assertNotIn(forbidden, completed.stdout)

    def test_unique_long_option_prefixes_are_not_hidden_success_modes(self) -> None:
        prefixes = (
            "--c",
            "--current",
            "--current-s",
            "--l",
            "--list",
            "--list-negative",
            "--he",
        )
        for prefix in prefixes:
            with self.subTest(prefix=prefix):
                completed = self._run(prefix)
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(completed.stdout, b"")
                self.assertEqual(completed.stderr, EXPECTED_ARGUMENT_ERROR_BYTES)

    def test_help_bytes_ignore_columns_and_python_io_encoding(self) -> None:
        environments = (
            {},
            {"COLUMNS": "20"},
            {"COLUMNS": "200"},
            {"PYTHONIOENCODING": "utf-16"},
            {"COLUMNS": "20", "PYTHONIOENCODING": "utf-16"},
        )
        for environment in environments:
            with self.subTest(environment=environment):
                first = self._run("--help", environment=environment)
                second = self._run("--help", environment=environment)
                self.assertEqual(first.returncode, 0)
                self.assertEqual(first.stderr, b"")
                self.assertEqual(first.stdout, second.stdout)
                self.assertEqual(first.stdout, EXPECTED_HELP_BYTES)

    def test_forbidden_values_after_valid_mode_are_never_reflected(self) -> None:
        attempts = (
            ("--root", "ROOT_VALUE_MUST_NOT_BE_REFLECTED"),
            ("--key", "KEY_VALUE_MUST_NOT_BE_REFLECTED"),
        )
        environments = (
            {},
            {"COLUMNS": "20"},
            {"COLUMNS": "200"},
            {"PYTHONIOENCODING": "utf-16"},
        )
        for option, sentinel in attempts:
            for environment in environments:
                with self.subTest(option=option, environment=environment):
                    first = self._run(
                        "--current-status",
                        option,
                        sentinel,
                        environment=environment,
                    )
                    second = self._run(
                        "--current-status",
                        option,
                        sentinel,
                        environment=environment,
                    )
                    self.assertEqual(first.returncode, 2)
                    self.assertEqual(first.stdout, b"")
                    self.assertEqual(first.stderr, second.stderr)
                    self.assertEqual(first.stderr, EXPECTED_ARGUMENT_ERROR_BYTES)
                    self.assertNotIn(sentinel.encode("ascii"), first.stderr)
                    self.assertNotIn(b"\r", first.stderr)
                    self.assertNotIn(b"\x00", first.stderr)

    def test_default_unknown_and_authority_injection_arguments_fail_at_argparse(
        self,
    ) -> None:
        attempts = (
            (),
            ("--unknown",),
            ("--current-status", "--list-negative-fixtures"),
            ("--path", "sentinel"),
            ("--key", "sentinel"),
            ("--root", "sentinel"),
            ("--external-root", "sentinel"),
            ("--signature", "sentinel"),
            ("--source", "sentinel"),
            ("--data", "sentinel"),
            ("--rate", "sentinel"),
            ("--output", "sentinel"),
        )
        for arguments in attempts:
            with self.subTest(arguments=arguments):
                completed = self._run(*arguments)
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(completed.stdout, b"")
                self.assertIn(b"error:", completed.stderr)


class GenerationZeroStaticBoundaryTests(unittest.TestCase):
    def test_production_and_cli_ast_have_no_external_io_or_dynamic_capability(
        self,
    ) -> None:
        self.assertTrue(MODULE_PATH.is_file())
        self.assertTrue(CLI_PATH.is_file())
        production = MODULE_PATH.read_text(encoding="utf-8")
        cli = CLI_PATH.read_text(encoding="utf-8")
        self.assertEqual(_capability_policy_violations(production), ())
        self.assertEqual(_capability_policy_violations(cli, cli=True), ())
        imported_modules = {
            node.module
            for node in ast.walk(ast.parse(production))
            if isinstance(node, ast.ImportFrom)
        }
        self.assertTrue(
            {
                "iclr2027.path_b_positive_intake_contract",
                "iclr2027.path_b_positive_intake_crypto",
                "iclr2027.path_b_positive_intake_science",
            }.issubset(imported_modules)
        )

    def test_ast_policy_rejects_structural_capability_observation_mutations(
        self,
    ) -> None:
        mutations = (
            "value = capability.root",
            "value = capability['root']",
            "value = iter(capability)",
            "value = bool(capability)",
            "value = str(capability)",
            "value = repr(capability)",
            "value = hash(capability)",
            "value = capability.__fspath__()",
            "value = getattr(capability, 'root')",
            "value = open(capability)",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                source = (
                    "class NeedsContextError(Exception):\n    pass\n"
                    "def validate_authenticated_path_b_intake(capability):\n"
                    f"    {mutation}\n"
                    "    raise NeedsContextError('external_root_missing')\n"
                )
                self.assertFalse(_authenticated_entrypoint_is_exact(source))

    def test_ast_policy_rejects_every_reviewed_false_green(self) -> None:
        production = MODULE_PATH.read_text(encoding="utf-8")
        cli = CLI_PATH.read_text(encoding="utf-8")
        production_mutations = (
            "import multiprocessing",
            "import webbrowser",
            "import marshal\nvalue = marshal.loads(b'x')",
            (
                "from cryptography.hazmat.primitives.asymmetric.ed25519 "
                "import Ed25519PrivateKey\nvalue = Ed25519PrivateKey.generate()"
            ),
            "def from_dict(value):\n    return value",
            "value = sys.modules.get('os')",
            "_CAPABILITY = json.load",
            "current_status = json.load",
        )
        cli_mutations = (
            "import multiprocessing",
            (
                "from cryptography.hazmat.primitives.asymmetric.ed25519 "
                "import Ed25519PrivateKey\nvalue = Ed25519PrivateKey.generate()"
            ),
            "def from_json(value):\n    return value",
            "sys.stderr.write('arbitrary')",
            "_CAPABILITY = sys.modules",
            "_CAPABILITY = sys.path",
        )
        for mutation in production_mutations:
            with self.subTest(target="production", mutation=mutation):
                self.assertTrue(
                    _capability_policy_violations(f"{production}\n{mutation}\n")
                )
        for mutation in cli_mutations:
            with self.subTest(target="cli", mutation=mutation):
                self.assertTrue(
                    _capability_policy_violations(
                        f"{cli}\n{mutation}\n",
                        cli=True,
                    )
                )

    def test_ast_policy_accepts_only_delete_then_external_root_missing_raise(
        self,
    ) -> None:
        accepted = (
            "class NeedsContextError(Exception):\n    pass\n"
            "def validate_authenticated_path_b_intake(capability: object):\n"
            "    del capability\n"
            "    raise NeedsContextError('external_root_missing')\n"
        )
        self.assertTrue(_authenticated_entrypoint_is_exact(accepted))
        variants = (
            accepted.replace("del capability\n", ""),
            accepted.replace("external_root_missing", "NEEDS_CONTEXT"),
            accepted.replace("del capability", "capability = None"),
            accepted.replace("raise NeedsContextError", "return NeedsContextError"),
            accepted.replace("capability: object", "capability: object, root=None"),
        )
        for source in variants:
            with self.subTest(source=source):
                self.assertFalse(_authenticated_entrypoint_is_exact(source))


class TaskSevenOrchestratorAdversarialTests(unittest.TestCase):
    def _run_cli(
        self,
        *arguments: str,
        environment: dict[str, str] | None = None,
        stdin_bytes: bytes | None = None,
        cwd: Path = ROOT,
    ) -> subprocess.CompletedProcess[bytes]:
        process_environment = dict(os.environ)
        if environment is not None:
            process_environment.update(environment)
        return subprocess.run(
            [sys.executable, "-E", "-B", str(CLI_PATH), *arguments],
            cwd=cwd,
            shell=False,
            input=stdin_bytes,
            capture_output=True,
            text=False,
            check=False,
            env=process_environment,
        )

    def test_extended_hostile_capability_is_not_observed_by_any_protocol(self) -> None:
        module = _module()
        hostile = _TaskSevenHostileCapability()
        with self.assertRaisesRegex(
            module.NeedsContextError,
            "^external_root_missing$",
        ):
            module.validate_authenticated_path_b_intake(hostile)
        self.assertEqual(hostile.observation_count, 0)

    def test_bootstrap_locator_key_path_and_mapping_injections_never_authorize(
        self,
    ) -> None:
        module = _module()
        attempts = (
            None,
            "ROOT_SENTINEL",
            b"KEY_SENTINEL",
            Path("LOCATOR_SENTINEL"),
            {"external_root": "ROOT_SENTINEL"},
            {"public_key": "KEY_SENTINEL", "signature": "SIG_SENTINEL"},
            ["locator", "rollback", "replay"],
        )
        baseline = module.current_status().to_dict()
        for index, attempt in enumerate(attempts):
            with self.subTest(index=index):
                with self.assertRaisesRegex(
                    module.NeedsContextError,
                    "^external_root_missing$",
                ):
                    module.validate_authenticated_path_b_intake(attempt)
                self.assertEqual(module.current_status().to_dict(), baseline)
        self.assertEqual(baseline["authority_mode"], "external_bootstrap_absent")
        self.assertEqual(baseline["status"], "no_go")
        self.assertEqual(baseline["empirical_status"], "no_go_needs_context")
        self.assertTrue(baseline["synthetic_only"])
        self.assertTrue(all(baseline[field] == 0 for field in EXPECTED_COUNTER_FIELDS))
        self.assertTrue(
            all(baseline[field] is False for field in EXPECTED_BOOLEAN_FIELDS)
        )

    def test_every_failure_family_preserves_identical_zero_observer_counters(
        self,
    ) -> None:
        module = _module()
        expected = module.current_status().to_dict()
        for reason_code in EXPECTED_REASON_CODES:
            closed_metadata = {
                "schema_version": (
                    "ace.iclr2027.path_b_positive_intake_attack_metadata.v1"
                ),
                "attack_id": reason_code,
                "expected_reason_family": reason_code,
                "required_outcome": "reject_without_authority",
            }
            with self.subTest(reason_code=reason_code):
                with self.assertRaisesRegex(
                    module.NeedsContextError,
                    "^external_root_missing$",
                ):
                    module.validate_authenticated_path_b_intake(closed_metadata)
                observed = module.current_status().to_dict()
                self.assertEqual(observed, expected)
                self.assertTrue(
                    all(observed[field] == 0 for field in EXPECTED_COUNTER_FIELDS)
                )
                self.assertTrue(
                    all(observed[field] is False for field in EXPECTED_BOOLEAN_FIELDS)
                )

    def test_help_cannot_short_circuit_mixed_authority_injection_arguments(
        self,
    ) -> None:
        attempts = (
            ("--help", "--root", "ROOT_SENTINEL"),
            (
                "--current-status",
                "--help",
                "--external-root",
                "ROOT_SENTINEL",
            ),
            ("-h", "--key", "KEY_SENTINEL"),
        )
        for arguments in attempts:
            with self.subTest(arguments=arguments):
                completed = self._run_cli(*arguments)
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(completed.stdout, b"")
                self.assertEqual(completed.stderr, EXPECTED_ARGUMENT_ERROR_BYTES)
                self.assertNotIn(b"SENTINEL", completed.stderr)

    def test_cli_ignores_stdin_environment_and_rejects_response_file_injection(
        self,
    ) -> None:
        module = _module()
        expected = (module.current_status().to_json() + "\n").encode("ascii")
        environments = (
            {
                "ACE_PATH_B_EXTERNAL_ROOT": "ENV_ROOT_SENTINEL",
                "ACE_PATH_B_SIGNING_KEY": "ENV_KEY_SENTINEL",
                "ACE_PATH_B_LOCATOR": "ENV_LOCATOR_SENTINEL",
            },
            {"PYTHONPROFILEIMPORTTIME": "1"},
            {"PYTHONWARNINGS": "error"},
            {"PYTHONIOENCODING": "utf-16"},
            {"PYTHONPATH": "ENV_PATH_SENTINEL"},
        )
        for environment in environments:
            for stdin_bytes in (
                b"--external-root STDIN_ROOT_SENTINEL\n",
                b"--key STDIN_KEY_SENTINEL\n",
            ):
                with self.subTest(environment=environment, stdin=stdin_bytes):
                    completed = self._run_cli(
                        "--current-status",
                        environment=environment,
                        stdin_bytes=stdin_bytes,
                        cwd=ROOT.parent,
                    )
                    self.assertEqual(completed.returncode, 0)
                    self.assertEqual(completed.stdout, expected)
                    self.assertEqual(completed.stderr, b"")
                    self.assertNotIn(b"SENTINEL", completed.stdout)

        response_file = self._run_cli("@ROOT_SENTINEL")
        self.assertEqual(response_file.returncode, 2)
        self.assertEqual(response_file.stdout, b"")
        self.assertEqual(response_file.stderr, EXPECTED_ARGUMENT_ERROR_BYTES)


if __name__ == "__main__":
    unittest.main()
