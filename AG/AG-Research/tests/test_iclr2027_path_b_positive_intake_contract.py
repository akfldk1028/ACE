import ast
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
import importlib
import json
from pathlib import Path
import sys
from types import ModuleType
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "iclr2027" / "path_b_positive_intake_contract.py"

LOCATOR_SCHEMA_VERSION = "ace.iclr2027.path_b_positive_intake_locator.v1"
INDEX_SCHEMA_VERSION = "ace.iclr2027.path_b_positive_intake_package_index.v1"
APPROVAL_SCHEMA_VERSION = "ace.iclr2027.path_b_external_role_approval.v1"
RESULT_SCHEMA_VERSION = "ace.iclr2027.path_b_positive_intake_result.v1"

LOCATOR_FIELDS = frozenset(
    {
        "schema_version",
        "locator_version",
        "locator_logical_id",
        "package_logical_id",
        "package_generation",
        "predecessor_locator_sha256",
        "trust_policy_sha256",
        "immutable_store_identity",
        "immutable_object_identity",
        "immutable_object_version",
        "package_root_physical_identity",
        "package_index_member_identity",
        "package_index_file_byte_count",
        "package_index_file_sha256",
        "task7_process_spec_custody_ref_sha256",
        "task5_scientific_parent_custody_ref_sha256s",
        "member_manifest_sha256",
        "pin_approval_manifest_sha256",
        "rotation_current_head_sha256",
        "verifier_challenge_sha256",
        "created_at_utc",
        "expires_at_utc",
        "locator_sha256",
    }
)

INDEX_FIELDS = frozenset(
    {
        "schema_version",
        "index_version",
        "package_logical_id",
        "package_generation",
        "task7_process_spec_custody_ref",
        "task5_scientific_parent_custody_refs",
        "core_triples",
        "referenced_members",
        "pin_approval_refs",
        "canonical_core_record_count",
        "artifact_count",
        "envelope_count",
        "pin_count",
        "review_count",
        "migration_receipt_pin_sha256",
        "index_sha256",
    }
)

APPROVAL_FIELDS = frozenset(
    {
        "schema_version",
        "approval_version",
        "approval_role",
        "approver_identity",
        "subject_role",
        "subject_logical_id",
        "subject_file_sha256",
        "decision",
        "approved_at_utc",
        "detached_message_domain",
        "signature_algorithm",
        "signing_key_id",
        "signing_public_key_member_identity",
        "signing_public_key_byte_count",
        "signing_public_key_sha256",
        "detached_signature_member_identity",
        "detached_signature_byte_count",
        "detached_signature_sha256",
        "approval_sha256",
    }
)

RESULT_FIELDS = frozenset(
    {
        "schema_version",
        "result_version",
        "input_refs",
        "input_counts",
        "stage_counters",
        "status",
        "reason_codes",
        "task6_vnext_commission_eligible",
        "source_access_authorized",
        "simulation_authorized",
        "paid_run_authorized",
        "official_result_eligible",
        "empirical_status",
        "result_sha256",
    }
)

CORE_TRIPLE_FIELDS = frozenset(
    {
        "role",
        "artifact_member_identity",
        "artifact_file_byte_count",
        "artifact_file_sha256",
        "envelope_member_identity",
        "envelope_file_byte_count",
        "envelope_file_sha256",
        "pin_member_identity",
        "pin_file_byte_count",
        "pin_file_sha256",
    }
)
REFERENCED_MEMBER_FIELDS = frozenset(
    {"member_kind", "member_identity", "file_byte_count", "file_sha256"}
)
PIN_APPROVAL_REF_FIELDS = frozenset(
    {
        "subject_role",
        "approval_member_identity",
        "approval_file_byte_count",
        "approval_file_sha256",
    }
)

CORE_ROLES = (
    "legacy_search_impossibility_declaration",
    "one_thesis_contract",
    "new_upstream_scientific_snapshot",
    "independent_science_migration_review",
    "independent_provenance_migration_review",
    "independent_security_migration_review",
    "provenance_migration_receipt",
)
SUBJECT_ROLES = CORE_ROLES + ("path_b_positive_intake_locator",)
APPROVAL_DOMAINS = {
    "responsible_owner": "ACE-ICLR2027-PATH-B-RESPONSIBLE-OWNER-APPROVAL-V1\x00",
    "external_scientist": "ACE-ICLR2027-PATH-B-EXTERNAL-SCIENTIST-APPROVAL-V1\x00",
    "custodian": "ACE-ICLR2027-PATH-B-CUSTODIAN-APPROVAL-V1\x00",
    "artifact_pin": "ACE-ICLR2027-PATH-B-ARTIFACT-PIN-APPROVAL-V1\x00",
    "locator_pin": "ACE-ICLR2027-PATH-B-LOCATOR-PIN-APPROVAL-V1\x00",
}
REFERENCED_MEMBER_KINDS = (
    "signing_public_key",
    "detached_signature",
    "verifier_executable",
    "platform_signature",
    "rotation",
    "legacy_search_evidence",
    "responsible_owner_approval",
    "external_scientist_approval",
    "custodian_approval",
    "pin_approval",
    "task7_process_spec_custody",
    "task5_scientific_parent_custody",
)
REASON_FAMILIES = (
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

HEX_A = "a" * 64
HEX_B = "b" * 64
HEX_C = "c" * 64
HEX_D = "d" * 64


def _contract():
    try:
        return importlib.import_module("iclr2027.path_b_positive_intake_contract")
    except ModuleNotFoundError as error:
        raise AssertionError("positive-intake contract module is absent") from error


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sealed_raw(payload: dict[str, object], self_field: str) -> bytes:
    body = dict(payload)
    body[self_field] = sha256(_canonical(body)).hexdigest()
    return _canonical(body) + b"\n"


def _mutated_contract(old: str, new: str) -> ModuleType:
    source = MODULE_PATH.read_text(encoding="utf-8")
    if source.count(old) != 1:
        raise AssertionError("production mutation anchor is not exact")
    mutant_name = "iclr2027.path_b_positive_intake_contract_test_mutant"
    mutant = ModuleType(mutant_name)
    mutant.__file__ = str(MODULE_PATH)
    mutant.__package__ = "iclr2027"
    sys.modules[mutant_name] = mutant
    exec(
        compile(source.replace(old, new, 1), str(MODULE_PATH), "exec"), mutant.__dict__
    )
    return mutant


def _locator_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": LOCATOR_SCHEMA_VERSION,
        "locator_version": 1,
        "locator_logical_id": "locator:alpha",
        "package_logical_id": "package:alpha",
        "package_generation": 1,
        "predecessor_locator_sha256": HEX_A,
        "trust_policy_sha256": HEX_B,
        "immutable_store_identity": "store:immutable",
        "immutable_object_identity": "object:alpha",
        "immutable_object_version": "version:1",
        "package_root_physical_identity": "volume:file-id",
        "package_index_member_identity": "members/index.json",
        "package_index_file_byte_count": 4096,
        "package_index_file_sha256": HEX_C,
        "task7_process_spec_custody_ref_sha256": HEX_D,
        "task5_scientific_parent_custody_ref_sha256s": [HEX_A, HEX_B, HEX_C],
        "member_manifest_sha256": HEX_D,
        "pin_approval_manifest_sha256": HEX_A,
        "rotation_current_head_sha256": HEX_B,
        "verifier_challenge_sha256": HEX_C,
        "created_at_utc": "2026-08-30T00:00:00Z",
        "expires_at_utc": "2026-09-30T00:00:00Z",
    }
    payload.update(overrides)
    return payload


def _digest(number: int) -> str:
    return f"{number:064x}"


def _core_triple(index: int, role: str) -> dict[str, object]:
    return {
        "role": role,
        "artifact_member_identity": f"core/{index}/artifact.json",
        "artifact_file_byte_count": 1000 + index,
        "artifact_file_sha256": _digest(10 + index),
        "envelope_member_identity": f"core/{index}/envelope.json",
        "envelope_file_byte_count": 2000 + index,
        "envelope_file_sha256": _digest(20 + index),
        "pin_member_identity": f"core/{index}/pin.json",
        "pin_file_byte_count": 3000 + index,
        "pin_file_sha256": _digest(30 + index),
    }


def _referenced_member(index: int = 0) -> dict[str, object]:
    return {
        "member_kind": "signing_public_key",
        "member_identity": f"members/public-key-{index}.bin",
        "file_byte_count": 32,
        "file_sha256": _digest(40 + index),
    }


def _pin_approval_ref(index: int, role: str) -> dict[str, object]:
    return {
        "subject_role": role,
        "approval_member_identity": f"approvals/pin-{index}.json",
        "approval_file_byte_count": 4000 + index,
        "approval_file_sha256": _digest(50 + index),
    }


def _index_payload(**overrides: object) -> dict[str, object]:
    pin_approval_refs = [
        _pin_approval_ref(index, role) for index, role in enumerate(CORE_ROLES)
    ]
    payload: dict[str, object] = {
        "schema_version": INDEX_SCHEMA_VERSION,
        "index_version": 1,
        "package_logical_id": "package:alpha",
        "package_generation": 1,
        "task7_process_spec_custody_ref": "custody:task7",
        "task5_scientific_parent_custody_refs": [
            "custody:task5:a",
            "custody:task5:b",
            "custody:task5:c",
        ],
        "core_triples": [
            _core_triple(index, role) for index, role in enumerate(CORE_ROLES)
        ],
        "referenced_members": [
            _referenced_member(),
            *(
                {
                    "member_kind": "pin_approval",
                    "member_identity": pin_ref["approval_member_identity"],
                    "file_byte_count": pin_ref["approval_file_byte_count"],
                    "file_sha256": pin_ref["approval_file_sha256"],
                }
                for pin_ref in pin_approval_refs
            ),
        ],
        "pin_approval_refs": pin_approval_refs,
        "canonical_core_record_count": 21,
        "artifact_count": 7,
        "envelope_count": 7,
        "pin_count": 7,
        "review_count": 3,
        "migration_receipt_pin_sha256": HEX_A,
    }
    payload.update(overrides)
    return payload


def _index_payload_with_pin_inventory() -> dict[str, object]:
    return _index_payload()


def _approval_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": APPROVAL_SCHEMA_VERSION,
        "approval_version": 1,
        "approval_role": "responsible_owner",
        "approver_identity": "owner:external",
        "subject_role": "one_thesis_contract",
        "subject_logical_id": "artifact:thesis",
        "subject_file_sha256": HEX_A,
        "decision": "approve",
        "approved_at_utc": "2026-08-30T00:00:00Z",
        "detached_message_domain": APPROVAL_DOMAINS["responsible_owner"],
        "signature_algorithm": "Ed25519",
        "signing_key_id": "key:owner",
        "signing_public_key_member_identity": "keys/owner.pub",
        "signing_public_key_byte_count": 32,
        "signing_public_key_sha256": HEX_B,
        "detached_signature_member_identity": "signatures/owner.sig",
        "detached_signature_byte_count": 64,
        "detached_signature_sha256": HEX_C,
    }
    payload.update(overrides)
    return payload


def _result_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "result_version": 1,
        "input_refs": {},
        "input_counts": {},
        "stage_counters": {},
        "status": "no_go",
        "reason_codes": ["external_root_missing"],
        "task6_vnext_commission_eligible": False,
        "source_access_authorized": False,
        "simulation_authorized": False,
        "paid_run_authorized": False,
        "official_result_eligible": False,
        "empirical_status": "no_go_needs_context",
    }
    payload.update(overrides)
    return payload


def _ast_capability_violations(source: str) -> list[str]:
    tree = ast.parse(source)
    allowed_plain_imports = {"json", "math", "re"}
    allowed_from_imports = {
        "dataclasses": {"dataclass"},
        "hashlib": {"sha256"},
    }
    allowed_direct_calls = {
        "ClosedSchema",
        "IntakeContractError",
        "PersistedRecord",
        "_canonical_json",
        "_canonical_utc",
        "_decode_canonical_record",
        "_fail",
        "_require_counter_map",
        "_require_exact_item",
        "_require_integer",
        "_require_positive_integer",
        "_require_string_map",
        "_require_unique_occurrences",
        "_safe_relative_member_identity",
        "_sha256_text",
        "_validate_approval",
        "_validate_index",
        "_validate_result",
        "_validate_schema_values",
        "_validate_tree",
        "_visible_ascii",
        "abs",
        "all",
        "any",
        "bool",
        "dataclass",
        "dict",
        "float",
        "frozenset",
        "int",
        "len",
        "ord",
        "range",
        "set",
        "sha256",
        "sorted",
        "tuple",
        "type",
    }
    allowed_attribute_calls = {
        "canonical_body.decode",
        "_SHORT_NAME_ALIAS.search",
        "_UTC_PATTERN.fullmatch",
        "json.dumps",
        "json.loads",
        "math.copysign",
        "math.isfinite",
        "matched.group",
        "member_hashes.extend",
        "member_identities.extend",
        "pin_approval_members.count",
        "pin_approval_references.count",
        "raw.count",
        "raw.startswith",
        "re.compile",
        "reason.encode",
        "self_hash_body.pop",
        "segment.endswith",
        "segment.partition",
        "stem.upper",
        "text.encode",
        "token.startswith",
        "value.casefold",
        "value.items",
        "value.split",
        "value.startswith",
    }
    allowed_module_attributes = {
        "json": {"JSONDecodeError", "dumps", "loads"},
        "math": {"copysign", "isfinite"},
        "re": {"IGNORECASE", "compile"},
    }
    forbidden_symbols = {
        "Path",
        "__import__",
        "compile",
        "delattr",
        "eval",
        "exec",
        "getattr",
        "globals",
        "hasattr",
        "importlib",
        "locals",
        "marshal",
        "open",
        "os",
        "pathlib",
        "pickle",
        "setattr",
        "shelve",
        "socket",
        "subprocess",
        "sys",
        "vars",
    }
    violations: list[str] = []
    canonical_functions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_canonical_json"
    ]
    canonical_dumps = (
        [
            node
            for node in ast.walk(canonical_functions[0])
            if isinstance(node, ast.Call) and ast.unparse(node.func) == "json.dumps"
        ]
        if len(canonical_functions) == 1
        else []
    )
    if len(canonical_dumps) != 1:
        violations.append("canonical-json-keyword-drift")
    else:
        try:
            observed_keywords = {
                keyword.arg: ast.literal_eval(keyword.value)
                for keyword in canonical_dumps[0].keywords
            }
        except (TypeError, ValueError):
            observed_keywords = {}
        if observed_keywords != {
            "ensure_ascii": False,
            "allow_nan": False,
            "sort_keys": True,
            "separators": (",", ":"),
        }:
            violations.append("canonical-json-keyword-drift")
    public_classes = tuple(
        node.name
        for node in tree.body
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_")
    )
    public_functions = tuple(
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    )
    top_level_assignments = tuple(
        target.id
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (node.targets if isinstance(node, ast.Assign) else (node.target,))
        if isinstance(target, ast.Name)
    )
    if public_classes != ("IntakeContractError", "ClosedSchema", "PersistedRecord"):
        violations.append("public-class-drift")
    if public_functions != ("parse_persisted_record", "parse_self_hashed_record"):
        violations.append("public-function-drift")
    if top_level_assignments != (
        "MAX_RECORD_BYTES",
        "MAX_JSON_DEPTH",
        "MAX_SAFE_INTEGER",
        "SealedRecord",
        "_LOCATOR_FIELDS",
        "LOCATOR_SCHEMA",
        "_INDEX_FIELDS",
        "PACKAGE_INDEX_SCHEMA",
        "_APPROVAL_FIELDS",
        "EXTERNAL_ROLE_APPROVAL_SCHEMA",
        "_RESULT_FIELDS",
        "RESULT_SCHEMA",
        "PathBPositiveIntakeLocatorV1",
        "PathBPositiveIntakePackageIndexV1",
        "PathBExternalRoleApprovalV1",
        "PathBPositiveIntakeResultV1",
        "_CORE_TRIPLE_FIELDS",
        "_CORE_TRIPLE_IDENTITIES",
        "_CORE_TRIPLE_COUNTS",
        "_CORE_TRIPLE_HASHES",
        "_REFERENCED_MEMBER_FIELDS",
        "_REFERENCED_MEMBER_IDENTITIES",
        "_REFERENCED_MEMBER_COUNTS",
        "_REFERENCED_MEMBER_HASHES",
        "_PIN_APPROVAL_REF_FIELDS",
        "_PIN_APPROVAL_REF_IDENTITIES",
        "_PIN_APPROVAL_REF_COUNTS",
        "_PIN_APPROVAL_REF_HASHES",
        "_APPROVAL_DOMAINS",
        "_CORE_ROLES",
        "_REFERENCED_MEMBER_KINDS",
        "_APPROVAL_SUBJECT_ROLES",
        "_UTC_PATTERN",
        "_WINDOWS_DEVICE_STEMS",
        "_SHORT_NAME_ALIAS",
        "_RESULT_REASON_FAMILIES",
    ):
        violations.append("module-assignment-drift")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in allowed_plain_imports or alias.asname is not None:
                    violations.append(f"forbidden import: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            allowed_names = allowed_from_imports.get(node.module or "", set())
            for alias in node.names:
                if alias.name not in allowed_names or alias.asname is not None:
                    violations.append(
                        f"forbidden from import: {node.module}.{alias.name}"
                    )
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            violations.append(f"forbidden dunder name: {node.id}")
        if isinstance(node, ast.Name) and node.id in forbidden_symbols:
            violations.append(f"forbidden capability symbol: {node.id}")
        if (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Store)
            and node.id in allowed_direct_calls
        ):
            violations.append(f"trusted call name rebound: {node.id}")
        if isinstance(node, ast.arg) and node.arg in allowed_direct_calls:
            violations.append(f"trusted call name shadowed by argument: {node.arg}")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            violations.append(f"forbidden dunder attribute: {node.attr}")
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id in allowed_module_attributes
            and node.attr not in allowed_module_attributes[node.value.id]
        ):
            violations.append(
                f"non-allowlisted module attribute: {node.value.id}.{node.attr}"
            )
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            if node.func.id not in allowed_direct_calls:
                violations.append(f"non-allowlisted call: {node.func.id}")
            continue
        if isinstance(node.func, ast.Attribute) and isinstance(
            node.func.value, ast.Name
        ):
            target = f"{node.func.value.id}.{node.func.attr}"
            if target not in allowed_attribute_calls:
                violations.append(f"non-allowlisted attribute call: {target}")
            continue
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "hexdigest"
            and isinstance(node.func.value, ast.Call)
            and isinstance(node.func.value.func, ast.Name)
            and node.func.value.func.id == "sha256"
        ):
            continue
        violations.append(f"non-allowlisted call target: {ast.dump(node.func)}")
    return violations


class PositiveIntakeCanonicalContractTests(unittest.TestCase):
    def _assert_rejected(self, raw: bytes, schema_name: str = "LOCATOR_SCHEMA") -> None:
        contract = _contract()
        with self.assertRaises(contract.IntakeContractError):
            contract.parse_persisted_record(raw, getattr(contract, schema_name))

    def _parse_accepted(self, raw: bytes, schema: object) -> object:
        contract = _contract()
        try:
            return contract.parse_persisted_record(raw, schema)
        except contract.IntakeContractError as error:
            self.fail(f"valid ruled schema was rejected: {error}")

    def _assert_module_rejects(
        self,
        contract: ModuleType,
        raw: bytes,
        schema_name: str,
    ) -> None:
        try:
            contract.parse_persisted_record(raw, getattr(contract, schema_name))
        except contract.IntakeContractError:
            return
        except Exception as error:
            self.fail(
                "weakened contract leaked "
                f"{type(error).__name__} instead of IntakeContractError"
            )
        self.fail("weakened contract accepted the isolated attack")

    def test_all_four_closed_v1_schemas_accept_only_their_exact_top_level_fields(
        self,
    ) -> None:
        contract = _contract()
        cases = (
            (
                _locator_payload(),
                "locator_sha256",
                contract.LOCATOR_SCHEMA,
                LOCATOR_FIELDS,
            ),
            (
                _index_payload(),
                "index_sha256",
                contract.PACKAGE_INDEX_SCHEMA,
                INDEX_FIELDS,
            ),
            (
                _approval_payload(),
                "approval_sha256",
                contract.EXTERNAL_ROLE_APPROVAL_SCHEMA,
                APPROVAL_FIELDS,
            ),
            (_result_payload(), "result_sha256", contract.RESULT_SCHEMA, RESULT_FIELDS),
        )
        for payload, self_field, schema, expected_fields in cases:
            with self.subTest(schema_version=payload["schema_version"]):
                raw = _sealed_raw(payload, self_field)
                parsed = self._parse_accepted(raw, schema)
                self.assertEqual(parsed.schema_version, payload["schema_version"])
                self.assertEqual(
                    set(json.loads(parsed.canonical_body)), expected_fields
                )

                missing = dict(payload)
                missing.pop(next(iter(expected_fields - {self_field})))
                with self.assertRaises(contract.IntakeContractError):
                    contract.parse_persisted_record(
                        _sealed_raw(missing, self_field), schema
                    )

                unknown = dict(payload)
                unknown["caller_supplied_override"] = "forbidden"
                with self.assertRaises(contract.IntakeContractError):
                    contract.parse_persisted_record(
                        _sealed_raw(unknown, self_field), schema
                    )

    def test_persisted_record_separates_raw_file_hash_from_unterminated_self_hash(
        self,
    ) -> None:
        contract = _contract()
        payload = _locator_payload()
        expected_self = sha256(_canonical(payload)).hexdigest()
        raw = _sealed_raw(payload, "locator_sha256")

        value = contract.parse_persisted_record(raw, contract.LOCATOR_SCHEMA)

        self.assertEqual(value.file_sha256, sha256(raw).hexdigest())
        self.assertEqual(value.self_sha256, expected_self)
        self.assertNotEqual(value.file_sha256, value.self_sha256)
        self.assertEqual(value.raw_bytes, raw)
        self.assertEqual(value.canonical_body, raw[:-1])
        with self.assertRaises(FrozenInstanceError):
            value.file_sha256 = HEX_A
        self.assertFalse(hasattr(value, "__dict__"))

    def test_wrong_self_hash_is_rejected(self) -> None:
        payload = _locator_payload()
        value = json.loads(_sealed_raw(payload, "locator_sha256"))
        value["locator_sha256"] = "0" * 64
        self._assert_rejected(_canonical(value) + b"\n")

    def test_exactly_one_terminal_lf_is_required(self) -> None:
        raw = _sealed_raw(_locator_payload(), "locator_sha256")
        for attacked in (raw[:-1], raw + b"\n", raw[:-1] + b"\r\n"):
            with self.subTest(attacked=attacked[-3:]):
                self._assert_rejected(attacked)

    def test_utf8_bom_and_invalid_utf8_are_rejected(self) -> None:
        raw = _sealed_raw(_locator_payload(), "locator_sha256")
        lone_surrogate = raw.replace(b"locator:alpha", b"locator:\\ud800", 1)
        for attacked in (
            b"\xef\xbb\xbf" + raw,
            raw[:-2] + b"\xff\n",
            lone_surrogate,
        ):
            with self.subTest(prefix=attacked[:3], suffix=attacked[-3:]):
                self._assert_rejected(attacked)

    def test_decoder_recursion_limit_is_normalized_to_contract_rejection(self) -> None:
        contract = _contract()
        raw = b"[" * 1100 + b"0" + b"]" * 1100 + b"\n"
        with self.assertRaises(contract.IntakeContractError):
            contract.parse_persisted_record(raw, contract.LOCATOR_SCHEMA)

    def test_duplicate_keys_are_rejected_at_root_and_nested_depth(self) -> None:
        raw = _sealed_raw(_locator_payload(), "locator_sha256")
        root_duplicate = raw.replace(
            b"{",
            b'{"locator_version":1,',
            1,
        )
        self._assert_rejected(root_duplicate)

        index = _sealed_raw(_index_payload(), "index_sha256")
        nested_duplicate = index.replace(
            b'"role":"legacy_search_impossibility_declaration"',
            (
                b'"role":"legacy_search_impossibility_declaration",'
                b'"role":"legacy_search_impossibility_declaration"'
            ),
            1,
        )
        self.assertNotEqual(nested_duplicate, index)
        self._assert_rejected(nested_duplicate, "PACKAGE_INDEX_SCHEMA")

    def test_insignificant_whitespace_and_unsorted_keys_are_rejected(self) -> None:
        raw = _sealed_raw(_locator_payload(), "locator_sha256")
        whitespace = raw.replace(b"{", b"{ ", 1)
        self._assert_rejected(whitespace)

        value = json.loads(raw)
        unsorted_value = dict(reversed(tuple(value.items())))
        unsorted = (
            json.dumps(
                unsorted_value,
                separators=(",", ":"),
                sort_keys=False,
            ).encode()
            + b"\n"
        )
        self.assertNotEqual(unsorted, raw)
        self._assert_rejected(unsorted)

    def test_nonfinite_numbers_and_negative_zero_are_rejected(self) -> None:
        cases = (
            _locator_payload(package_generation=float("nan")),
            _locator_payload(package_generation=float("inf")),
            _locator_payload(package_generation=float("-inf")),
            _locator_payload(package_generation=-0.0),
        )
        for payload in cases:
            with self.subTest(value=payload["package_generation"]):
                self._assert_rejected(_sealed_raw(payload, "locator_sha256"))

    def test_integer_fields_reject_boolean_float_negative_and_large_integer(
        self,
    ) -> None:
        for value in (True, 1.0, -1, 2**53):
            with self.subTest(value=value):
                raw = _sealed_raw(
                    _locator_payload(package_generation=value),
                    "locator_sha256",
                )
                self._assert_rejected(raw)

    def test_json_depth_is_bounded_and_boundary_is_deterministic(self) -> None:
        contract = _contract()
        depth_33: object = "leaf"
        for _ in range(32):
            depth_33 = [depth_33]
        rejected = _sealed_raw(
            _index_payload(referenced_members=depth_33),
            "index_sha256",
        )
        with self.assertRaises(contract.IntakeContractError):
            contract.parse_persisted_record(rejected, contract.PACKAGE_INDEX_SCHEMA)

    def test_record_size_is_bounded(self) -> None:
        huge_identity = "x" * (1024 * 1024)
        raw = _sealed_raw(
            _locator_payload(locator_logical_id=huge_identity),
            "locator_sha256",
        )
        self._assert_rejected(raw)

    def test_exact_schema_and_record_version_one_are_required(self) -> None:
        contract = _contract()
        cases = (
            (
                contract.LOCATOR_SCHEMA,
                _locator_payload,
                "locator_sha256",
                "locator_version",
            ),
            (
                contract.PACKAGE_INDEX_SCHEMA,
                _index_payload,
                "index_sha256",
                "index_version",
            ),
            (
                contract.EXTERNAL_ROLE_APPROVAL_SCHEMA,
                _approval_payload,
                "approval_sha256",
                "approval_version",
            ),
            (
                contract.RESULT_SCHEMA,
                _result_payload,
                "result_sha256",
                "result_version",
            ),
        )
        for schema, factory, self_field, version_field in cases:
            for version in (0, 2, True):
                with self.subTest(schema=schema, version=version):
                    payload = factory(**{version_field: version})
                    with self.assertRaises(contract.IntakeContractError):
                        contract.parse_persisted_record(
                            _sealed_raw(payload, self_field),
                            schema,
                        )

        wrong_schema = _locator_payload(schema_version=INDEX_SCHEMA_VERSION)
        with self.assertRaises(contract.IntakeContractError):
            contract.parse_persisted_record(
                _sealed_raw(wrong_schema, "locator_sha256"),
                contract.LOCATOR_SCHEMA,
            )

    def test_identity_fields_require_nonempty_visible_ascii_without_spaces(
        self,
    ) -> None:
        contract = _contract()
        for value in ("", "owner identity", "owner\nidentity", "owner:é"):
            with self.subTest(value=value):
                payload = _locator_payload(locator_logical_id=value)
                with self.assertRaises(contract.IntakeContractError):
                    contract.parse_persisted_record(
                        _sealed_raw(payload, "locator_sha256"),
                        contract.LOCATOR_SCHEMA,
                    )

    def test_sha256_fields_are_exact_lowercase_hex(self) -> None:
        contract = _contract()
        for value in ("a" * 63, "A" * 64, "g" * 64, 7):
            with self.subTest(value=value):
                payload = _locator_payload(trust_policy_sha256=value)
                with self.assertRaises(contract.IntakeContractError):
                    contract.parse_persisted_record(
                        _sealed_raw(payload, "locator_sha256"),
                        contract.LOCATOR_SCHEMA,
                    )

    def test_array_shape_and_nested_unsupported_native_values_fail_closed(self) -> None:
        contract = _contract()
        wrong_parent_shape = _locator_payload(
            task5_scientific_parent_custody_ref_sha256s=[HEX_A, HEX_B]
        )
        with self.assertRaises(contract.IntakeContractError):
            contract.parse_persisted_record(
                _sealed_raw(wrong_parent_shape, "locator_sha256"),
                contract.LOCATOR_SCHEMA,
            )

        null_nested = _result_payload(input_refs={"locator": None})
        with self.assertRaises(contract.IntakeContractError):
            contract.parse_persisted_record(
                _sealed_raw(null_nested, "result_sha256"),
                contract.RESULT_SCHEMA,
            )

    def test_package_index_rejects_the_exact_independent_review_payload(self) -> None:
        contract = _contract()
        payload = _index_payload(
            core_triples=[{"arbitrary": [True, 3.5, {"nested": "value"}]}],
            referenced_members=["free-form-member"],
            pin_approval_refs=[False],
            canonical_core_record_count=0,
            artifact_count=999,
            envelope_count=1,
            pin_count=2,
            review_count=4,
            task5_scientific_parent_custody_refs=["same", "same", "same"],
        )
        with self.assertRaises(contract.IntakeContractError):
            contract.parse_persisted_record(
                _sealed_raw(payload, "index_sha256"),
                contract.PACKAGE_INDEX_SCHEMA,
            )

    def test_package_index_nested_items_have_exact_closed_shapes_and_leaf_types(
        self,
    ) -> None:
        contract = _contract()
        contract.parse_persisted_record(
            _sealed_raw(_index_payload(), "index_sha256"),
            contract.PACKAGE_INDEX_SCHEMA,
        )

        missing_core = _core_triple(0, CORE_ROLES[0])
        missing_core.pop("artifact_file_sha256")
        unknown_core = _core_triple(0, CORE_ROLES[0])
        unknown_core["caller_override"] = "forbidden"
        bad_core_count = _core_triple(0, CORE_ROLES[0])
        bad_core_count["artifact_file_byte_count"] = 1.5
        bad_core_identity = _core_triple(0, CORE_ROLES[0])
        bad_core_identity["artifact_member_identity"] = "artifact with space"
        missing_member = _referenced_member()
        missing_member.pop("file_sha256")
        unknown_member = _referenced_member()
        unknown_member["freeform"] = []
        bad_member_hash = _referenced_member()
        bad_member_hash["file_sha256"] = "A" * 64
        missing_pin_ref = _pin_approval_ref(0, CORE_ROLES[0])
        missing_pin_ref.pop("approval_file_sha256")

        attacks = (
            {"core_triples": [missing_core] + _index_payload()["core_triples"][1:]},
            {"core_triples": [unknown_core] + _index_payload()["core_triples"][1:]},
            {"core_triples": [bad_core_count] + _index_payload()["core_triples"][1:]},
            {
                "core_triples": [bad_core_identity]
                + _index_payload()["core_triples"][1:]
            },
            {"core_triples": ["not-a-triple"] * 7},
            {"referenced_members": [missing_member]},
            {"referenced_members": [unknown_member]},
            {"referenced_members": [bad_member_hash]},
            {"referenced_members": ["free-form-member"]},
            {
                "pin_approval_refs": [missing_pin_ref]
                + _index_payload()["pin_approval_refs"][1:]
            },
            {"pin_approval_refs": [False] * 7},
        )
        for attack in attacks:
            with self.subTest(attack=attack):
                payload = _index_payload(**attack)
                with self.assertRaises(contract.IntakeContractError):
                    contract.parse_persisted_record(
                        _sealed_raw(payload, "index_sha256"),
                        contract.PACKAGE_INDEX_SCHEMA,
                    )

    def test_package_index_closes_counts_cardinality_and_required_uniqueness(
        self,
    ) -> None:
        contract = _contract()
        attacks = (
            {"canonical_core_record_count": 0},
            {"artifact_count": 999},
            {"envelope_count": 1},
            {"pin_count": 2},
            {"review_count": 4},
            {"core_triples": _index_payload()["core_triples"][:-1]},
            {"pin_approval_refs": _index_payload()["pin_approval_refs"][:-1]},
            {"referenced_members": []},
            {
                "task5_scientific_parent_custody_refs": [
                    "custody:same",
                    "custody:same",
                    "custody:same",
                ]
            },
            {"referenced_members": [_referenced_member(), _referenced_member()]},
        )
        for attack in attacks:
            with self.subTest(attack=attack):
                payload = _index_payload(**attack)
                with self.assertRaises(contract.IntakeContractError):
                    contract.parse_persisted_record(
                        _sealed_raw(payload, "index_sha256"),
                        contract.PACKAGE_INDEX_SCHEMA,
                    )

    def test_package_index_nested_counts_are_positive_native_safe_integers(
        self,
    ) -> None:
        contract = _contract()
        for field, container_name, item_factory in (
            (
                "artifact_file_byte_count",
                "core_triples",
                lambda: _core_triple(0, CORE_ROLES[0]),
            ),
            ("file_byte_count", "referenced_members", _referenced_member),
            (
                "approval_file_byte_count",
                "pin_approval_refs",
                lambda: _pin_approval_ref(0, CORE_ROLES[0]),
            ),
        ):
            for value in (0, True, 2**53):
                with self.subTest(field=field, value=value):
                    item = item_factory()
                    item[field] = value
                    payload = _index_payload()
                    items = list(payload[container_name])
                    items[0] = item
                    payload[container_name] = items
                    with self.assertRaises(contract.IntakeContractError):
                        contract.parse_persisted_record(
                            _sealed_raw(payload, "index_sha256"),
                            contract.PACKAGE_INDEX_SCHEMA,
                        )

    def test_approval_accepts_only_the_exact_role_domain_and_subject_families(
        self,
    ) -> None:
        contract = _contract()
        for role, domain in APPROVAL_DOMAINS.items():
            with self.subTest(role=role):
                payload = _approval_payload(
                    approval_role=role,
                    subject_role=(
                        "path_b_positive_intake_locator"
                        if role == "locator_pin"
                        else "one_thesis_contract"
                    ),
                    detached_message_domain=domain,
                )
                self._parse_accepted(
                    _sealed_raw(payload, "approval_sha256"),
                    contract.EXTERNAL_ROLE_APPROVAL_SCHEMA,
                )

        for subject_role in SUBJECT_ROLES:
            with self.subTest(subject_role=subject_role):
                payload = _approval_payload(subject_role=subject_role)
                self._parse_accepted(
                    _sealed_raw(payload, "approval_sha256"),
                    contract.EXTERNAL_ROLE_APPROVAL_SCHEMA,
                )

        for role, wrong_domain in zip(
            APPROVAL_DOMAINS,
            tuple(APPROVAL_DOMAINS.values())[1:] + tuple(APPROVAL_DOMAINS.values())[:1],
            strict=True,
        ):
            with self.subTest(role=role, wrong_domain=wrong_domain):
                payload = _approval_payload(
                    approval_role=role,
                    detached_message_domain=wrong_domain,
                )
                with self.assertRaises(contract.IntakeContractError):
                    contract.parse_persisted_record(
                        _sealed_raw(payload, "approval_sha256"),
                        contract.EXTERNAL_ROLE_APPROVAL_SCHEMA,
                    )

    def test_approval_rejects_the_exact_independent_review_payload(self) -> None:
        contract = _contract()
        payload = _approval_payload(
            approval_role="caller_minted_admin",
            subject_role="caller_minted_subject",
            decision="unreviewed",
            detached_message_domain="FAKE-DOMAIN",
            signature_algorithm="RSA",
            signing_public_key_byte_count=0,
            detached_signature_byte_count=1,
        )
        with self.assertRaises(contract.IntakeContractError):
            contract.parse_persisted_record(
                _sealed_raw(payload, "approval_sha256"),
                contract.EXTERNAL_ROLE_APPROVAL_SCHEMA,
            )

    def test_approval_local_leaf_values_and_ed25519_counts_are_exact(self) -> None:
        contract = _contract()
        attacks = (
            {"approval_role": "caller_minted_role"},
            {"subject_role": "caller_minted_subject"},
            {"decision": "approved"},
            {"signature_algorithm": "RSA"},
            {"signing_public_key_byte_count": 31},
            {"detached_signature_byte_count": 63},
        )
        for attack in attacks:
            with self.subTest(attack=attack):
                payload = _approval_payload(**attack)
                with self.assertRaises(contract.IntakeContractError):
                    contract.parse_persisted_record(
                        _sealed_raw(payload, "approval_sha256"),
                        contract.EXTERNAL_ROLE_APPROVAL_SCHEMA,
                    )

    def test_approval_isolated_leaf_checks_are_mutation_sensitive(self) -> None:
        cases = (
            (
                "    if type(role) is not str or role not in _APPROVAL_DOMAINS:\n"
                '        _fail("canonical_file_encoding_failed")\n',
                {"approval_role": "caller_minted_role"},
            ),
            (
                '    if payload["subject_role"] not in _APPROVAL_SUBJECT_ROLES:\n'
                '        _fail("canonical_file_encoding_failed")\n',
                {"subject_role": "caller_minted_subject"},
            ),
            (
                '    if payload["decision"] != "approve":\n'
                '        _fail("canonical_file_encoding_failed")\n',
                {"decision": "approved"},
            ),
            (
                '    if payload["signature_algorithm"] != "Ed25519":\n'
                '        _fail("canonical_file_encoding_failed")\n',
                {"signature_algorithm": "RSA"},
            ),
            (
                '    if payload["signing_public_key_byte_count"] != 32:\n'
                '        _fail("canonical_file_encoding_failed")\n',
                {"signing_public_key_byte_count": 31},
            ),
            (
                '    if payload["detached_signature_byte_count"] != 64:\n'
                '        _fail("canonical_file_encoding_failed")\n',
                {"detached_signature_byte_count": 63},
            ),
        )
        for check, attack in cases:
            with self.subTest(attack=attack):
                mutant = _mutated_contract(check, "")
                raw = _sealed_raw(_approval_payload(**attack), "approval_sha256")
                with self.assertRaises(AssertionError):
                    self._assert_module_rejects(
                        mutant,
                        raw,
                        "EXTERNAL_ROLE_APPROVAL_SCHEMA",
                    )

    def test_reason_codes_are_closed_unique_byte_sorted_visible_ascii(self) -> None:
        contract = _contract()
        for values in ([], list(REASON_FAMILIES)):
            with self.subTest(valid_values=values):
                payload = _result_payload(reason_codes=values)
                self._parse_accepted(
                    _sealed_raw(payload, "result_sha256"),
                    contract.RESULT_SCHEMA,
                )

        for values in (
            [REASON_FAMILIES[1], REASON_FAMILIES[0]],
            [REASON_FAMILIES[0], REASON_FAMILIES[0]],
            ["syntactic_only"],
        ):
            with self.subTest(values=values):
                payload = _result_payload(reason_codes=values)
                with self.assertRaises(contract.IntakeContractError):
                    contract.parse_persisted_record(
                        _sealed_raw(payload, "result_sha256"),
                        contract.RESULT_SCHEMA,
                    )

    def test_reason_order_and_uniqueness_checks_are_mutation_sensitive(self) -> None:
        cases = (
            (
                "    if len(reasons) != len(set(reasons)):\n"
                '        _fail("canonical_file_encoding_failed")\n',
                [REASON_FAMILIES[0], REASON_FAMILIES[0]],
            ),
            (
                "    if reasons != sorted(reasons, key=lambda reason: "
                'reason.encode("ascii")):\n'
                '        _fail("canonical_file_encoding_failed")\n',
                [REASON_FAMILIES[1], REASON_FAMILIES[0]],
            ),
        )
        for check, reasons in cases:
            with self.subTest(reasons=reasons):
                mutant = _mutated_contract(check, "")
                raw = _sealed_raw(
                    _result_payload(reason_codes=reasons),
                    "result_sha256",
                )
                with self.assertRaises(AssertionError):
                    self._assert_module_rejects(mutant, raw, "RESULT_SCHEMA")

    def test_result_allows_empty_undocumented_maps_and_reason_list(self) -> None:
        contract = _contract()
        payload = _result_payload(
            input_refs={},
            input_counts={},
            stage_counters={},
            reason_codes=[],
        )
        self._parse_accepted(
            _sealed_raw(payload, "result_sha256"),
            contract.RESULT_SCHEMA,
        )

    def test_result_rejects_exact_reserved_generation1_success_tuple(self) -> None:
        contract = _contract()
        payload = _result_payload(
            status="authenticated_path_b_package_ready_for_separate_task6_vnext_authority",
            task6_vnext_commission_eligible=True,
            input_refs={},
            input_counts={},
            stage_counters={},
            reason_codes=[],
        )
        with self.assertRaises(contract.IntakeContractError):
            contract.parse_persisted_record(
                _sealed_raw(payload, "result_sha256"),
                contract.RESULT_SCHEMA,
            )

    def test_reserved_generation1_tuple_rejection_is_mutation_sensitive(self) -> None:
        anchor = "def _validate_result(payload: dict[str, object]) -> None:\n"
        weakening = anchor + (
            "    if (\n"
            '        payload["status"]\n'
            '        == "authenticated_path_b_package_ready_for_separate_task6_vnext_authority"\n'
            '        and payload["task6_vnext_commission_eligible"] is True\n'
            '        and payload["source_access_authorized"] is False\n'
            '        and payload["simulation_authorized"] is False\n'
            '        and payload["paid_run_authorized"] is False\n'
            '        and payload["official_result_eligible"] is False\n'
            '        and payload["empirical_status"] == "no_go_needs_context"\n'
            '        and payload["input_refs"] == {}\n'
            '        and payload["input_counts"] == {}\n'
            '        and payload["stage_counters"] == {}\n'
            '        and payload["reason_codes"] == []\n'
            "    ):\n"
            "        return\n"
        )
        mutant = _mutated_contract(anchor, weakening)
        payload = _result_payload(
            status="authenticated_path_b_package_ready_for_separate_task6_vnext_authority",
            task6_vnext_commission_eligible=True,
            input_refs={},
            input_counts={},
            stage_counters={},
            reason_codes=[],
        )
        raw = _sealed_raw(payload, "result_sha256")
        with self.assertRaises(AssertionError):
            self._assert_module_rejects(mutant, raw, "RESULT_SCHEMA")

    def test_result_accepts_only_the_generation_zero_no_go_profile(self) -> None:
        contract = _contract()
        contract.parse_persisted_record(
            _sealed_raw(_result_payload(), "result_sha256"),
            contract.RESULT_SCHEMA,
        )

        attacks = (
            {
                "status": "authenticated_path_b_package_ready_for_separate_task6_vnext_authority"
            },
            {"empirical_status": "empirical_success"},
            {"task6_vnext_commission_eligible": True},
            {"source_access_authorized": True},
            {"simulation_authorized": True},
            {"paid_run_authorized": True},
            {"official_result_eligible": True},
            {
                "status": "authenticated_path_b_package_ready_for_separate_task6_vnext_authority",
                "task6_vnext_commission_eligible": True,
            },
        )
        for attack in attacks:
            with self.subTest(attack=attack):
                payload = _result_payload(**attack)
                with self.assertRaises(contract.IntakeContractError):
                    contract.parse_persisted_record(
                        _sealed_raw(payload, "result_sha256"),
                        contract.RESULT_SCHEMA,
                    )

    def test_boolean_fields_require_native_booleans(self) -> None:
        contract = _contract()
        for value in (0, 1, "false", None):
            with self.subTest(value=value):
                payload = _result_payload(source_access_authorized=value)
                with self.assertRaises(contract.IntakeContractError):
                    contract.parse_persisted_record(
                        _sealed_raw(payload, "result_sha256"),
                        contract.RESULT_SCHEMA,
                    )

    def test_result_nested_maps_are_type_closed_without_inventing_success_semantics(
        self,
    ) -> None:
        contract = _contract()
        attacks = (
            {"input_refs": {"locator": "contains space"}},
            {"input_refs": {"locator": "locator:é"}},
            {"input_counts": {"artifact_count": -1}},
            {"input_counts": {"artifact_count": True}},
            {"stage_counters": {"member_read_count": 2**53}},
        )
        for attack in attacks:
            with self.subTest(attack=attack):
                payload = _result_payload(**attack)
                with self.assertRaises(contract.IntakeContractError):
                    contract.parse_persisted_record(
                        _sealed_raw(payload, "result_sha256"),
                        contract.RESULT_SCHEMA,
                    )

    def test_parser_rejects_nonbytes_and_non_schema_inputs(self) -> None:
        contract = _contract()
        raw = _sealed_raw(_locator_payload(), "locator_sha256")
        for value in (raw.decode(), bytearray(raw), memoryview(raw)):
            with (
                self.subTest(value_type=type(value).__name__),
                self.assertRaises(contract.IntakeContractError),
            ):
                contract.parse_persisted_record(value, contract.LOCATOR_SCHEMA)
        with self.assertRaises(contract.IntakeContractError):
            contract.parse_persisted_record(raw, object())
        with self.assertRaises(contract.IntakeContractError):
            contract.parse_persisted_record(raw, replace(contract.LOCATOR_SCHEMA))

    def test_module_ast_has_no_generation_zero_capabilities(self) -> None:
        _contract()
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertEqual(_ast_capability_violations(source), [])

    def test_ast_oracle_rejects_builtin_dynamic_reflection_and_capability_escapes(
        self,
    ) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertEqual(_ast_capability_violations(source), [])
        mutations = (
            '__builtins__["open"]("forbidden.txt")',
            '__builtins__["__import__"]("os").getcwd()',
            "object.__subclasses__()",
            'vars(__builtins__)["open"]("forbidden.txt")',
            'eval("1 + 1")',
            '__import__("os")',
            "import os\nos.getcwd()",
            'from pathlib import Path\nPath("x").read_text()',
            "os.environ",
            "subprocess.PIPE",
            "socket.AF_INET",
            "Path.home",
            "escape = json.load",
            "escape = json.dump",
            "dict = json.load\ndict(None)",
            "sha256 = json.dump\nsha256({}, None)",
            "escape = math.sqrt",
            "decoder = json.JSONDecoder",
            "def from_json(value):\n    return value",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assertTrue(_ast_capability_violations(f"{source}\n{mutation}\n"))


class TaskSevenContractAdversarialTests(unittest.TestCase):
    def _assert_rejected(
        self,
        payload: dict[str, object],
        self_field: str,
        schema_name: str,
    ) -> None:
        contract = _contract()
        with self.assertRaises(contract.IntakeContractError):
            contract.parse_persisted_record(
                _sealed_raw(payload, self_field),
                getattr(contract, schema_name),
            )

    def test_canonical_file_self_hash_and_exact_version_attack_matrix(self) -> None:
        contract = _contract()
        valid = _sealed_raw(_locator_payload(), "locator_sha256")
        decoded = json.loads(valid)
        decoded["locator_sha256"] = sha256(valid).hexdigest()
        raw_hash_substituted_for_self_hash = _canonical(decoded) + b"\n"
        duplicate_schema_key = valid.replace(
            b'{"created_at_utc":',
            (
                b'{"schema_version":"'
                + LOCATOR_SCHEMA_VERSION.encode("ascii")
                + b'","created_at_utc":'
            ),
            1,
        )
        attacks = (
            raw_hash_substituted_for_self_hash,
            duplicate_schema_key,
            valid[:-1],
            valid[:-1] + b"\r\n",
            _sealed_raw(_locator_payload(locator_version=2), "locator_sha256"),
            _sealed_raw(
                _locator_payload(
                    schema_version="ace.iclr2027.path_b_positive_intake_locator.v2"
                ),
                "locator_sha256",
            ),
        )
        for index, raw in enumerate(attacks):
            with self.subTest(index=index):
                with self.assertRaises(contract.IntakeContractError):
                    contract.parse_persisted_record(raw, contract.LOCATOR_SCHEMA)

    def test_locator_local_generation_time_and_parent_census_attacks_reject(
        self,
    ) -> None:
        contract = _contract()
        contract.parse_persisted_record(
            _sealed_raw(
                _locator_payload(
                    created_at_utc="2028-02-29T23:59:59Z",
                    expires_at_utc="2028-03-01T00:00:00Z",
                ),
                "locator_sha256",
            ),
            contract.LOCATOR_SCHEMA,
        )
        attacks = (
            {"task5_scientific_parent_custody_ref_sha256s": [HEX_A, HEX_A, HEX_C]},
            {"package_generation": 0},
            {"package_index_file_byte_count": 0},
            {"created_at_utc": "tomorrow"},
            {"created_at_utc": "2026-08-30T00:00:00+00:00"},
            {"created_at_utc": "2026-02-30T00:00:00Z"},
            {"expires_at_utc": "2026-08-30T00:00:00Z"},
            {"expires_at_utc": "2026-08-29T23:59:59Z"},
        )
        for index, attack in enumerate(attacks):
            with self.subTest(index=index):
                self._assert_rejected(
                    _locator_payload(**attack),
                    "locator_sha256",
                    "LOCATOR_SCHEMA",
                )

    def test_index_nested_member_and_pin_reference_census_attacks_reject(
        self,
    ) -> None:
        base = _index_payload()
        core_identity_alias = [dict(item) for item in base["core_triples"]]
        core_identity_alias[1]["artifact_member_identity"] = core_identity_alias[0][
            "artifact_member_identity"
        ]
        core_hash_alias = [dict(item) for item in base["core_triples"]]
        core_hash_alias[1]["artifact_file_sha256"] = core_hash_alias[0][
            "artifact_file_sha256"
        ]
        pin_identity_alias = [dict(item) for item in base["pin_approval_refs"]]
        pin_identity_alias[1]["approval_member_identity"] = pin_identity_alias[0][
            "approval_member_identity"
        ]
        pin_hash_alias = [dict(item) for item in base["pin_approval_refs"]]
        pin_hash_alias[1]["approval_file_sha256"] = pin_hash_alias[0][
            "approval_file_sha256"
        ]
        unknown_pin_subject = [dict(item) for item in base["pin_approval_refs"]]
        unknown_pin_subject[0]["subject_role"] = "caller_minted_role"
        referenced_hash_alias = [_referenced_member(0), _referenced_member(1)]
        referenced_hash_alias[1]["file_sha256"] = referenced_hash_alias[0][
            "file_sha256"
        ]
        attacks = (
            {"core_triples": core_identity_alias},
            {"core_triples": core_hash_alias},
            {"pin_approval_refs": pin_identity_alias},
            {"pin_approval_refs": pin_hash_alias},
            {"pin_approval_refs": unknown_pin_subject},
            {"referenced_members": referenced_hash_alias},
            {"package_generation": 0},
        )
        for index, attack in enumerate(attacks):
            with self.subTest(index=index):
                self._assert_rejected(
                    _index_payload(**attack),
                    "index_sha256",
                    "PACKAGE_INDEX_SCHEMA",
                )

    def test_member_identity_schema_rejects_path_alias_and_device_attacks(
        self,
    ) -> None:
        hostile_members = (
            "../index.json",
            "/absolute/index.json",
            "C:/root/index.json",
            "\\\\server\\share\\index.json",
            "members/CON",
            "members/con.txt",
            "members/COM1.log",
            "members/PROGRA~1",
            "members/file~1.txt",
            "members//double.json",
            "members/./dot.json",
            "members/../parent.json",
            "members/trailing.",
            "members/trailing ",
            "members/file.bin:stream",
        )
        for member in hostile_members:
            with self.subTest(container="locator", member=member):
                self._assert_rejected(
                    _locator_payload(package_index_member_identity=member),
                    "locator_sha256",
                    "LOCATOR_SCHEMA",
                )

            core = [dict(item) for item in _index_payload()["core_triples"]]
            core[0]["artifact_member_identity"] = member
            with self.subTest(container="core", member=member):
                self._assert_rejected(
                    _index_payload(core_triples=core),
                    "index_sha256",
                    "PACKAGE_INDEX_SCHEMA",
                )

        casefold_members = [_referenced_member(0), _referenced_member(1)]
        casefold_members[0]["member_identity"] = "members/A.bin"
        casefold_members[1]["member_identity"] = "members/a.bin"
        with self.subTest(container="index_casefold_collision"):
            self._assert_rejected(
                _index_payload(referenced_members=casefold_members),
                "index_sha256",
                "PACKAGE_INDEX_SCHEMA",
            )

        cross_group_referenced = [_referenced_member(0)]
        cross_group_referenced[0]["member_identity"] = "CORE/0/ARTIFACT.JSON"
        with self.subTest(container="cross_group_casefold_collision"):
            self._assert_rejected(
                _index_payload(referenced_members=cross_group_referenced),
                "index_sha256",
                "PACKAGE_INDEX_SCHEMA",
            )

        for field, member in (
            ("signing_public_key_member_identity", "../outside.pub"),
            (
                "detached_signature_member_identity",
                "signatures/file.sig:stream",
            ),
        ):
            with self.subTest(container="approval", field=field):
                self._assert_rejected(
                    _approval_payload(**{field: member}),
                    "approval_sha256",
                    "EXTERNAL_ROLE_APPROVAL_SCHEMA",
                )

    def test_numeric_tail_aliases_and_console_devices_reject_everywhere(
        self,
    ) -> None:
        hostile_members = (
            "members/ABCDE~10",
            "members/A~123456",
            "members/CONIN$",
            "members/CONOUT$",
        )
        for member in hostile_members:
            with self.subTest(container="locator", member=member):
                self._assert_rejected(
                    _locator_payload(package_index_member_identity=member),
                    "locator_sha256",
                    "LOCATOR_SCHEMA",
                )

            core = [dict(item) for item in _index_payload()["core_triples"]]
            core[0]["artifact_member_identity"] = member
            with self.subTest(container="core", member=member):
                self._assert_rejected(
                    _index_payload(core_triples=core),
                    "index_sha256",
                    "PACKAGE_INDEX_SCHEMA",
                )

            referenced = [_referenced_member()]
            referenced[0]["member_identity"] = member
            with self.subTest(container="referenced", member=member):
                self._assert_rejected(
                    _index_payload(referenced_members=referenced),
                    "index_sha256",
                    "PACKAGE_INDEX_SCHEMA",
                )

            for field in (
                "signing_public_key_member_identity",
                "detached_signature_member_identity",
            ):
                with self.subTest(container="approval", field=field, member=member):
                    self._assert_rejected(
                        _approval_payload(**{field: member}),
                        "approval_sha256",
                        "EXTERNAL_ROLE_APPROVAL_SCHEMA",
                    )

    def test_tilde_and_console_like_nonaliases_remain_valid(self) -> None:
        contract = _contract()
        for member in (
            "members/ABCDE~A0",
            "members/A~0",
            "members/CONSOLE.txt",
            "members/CONIN.txt",
        ):
            with self.subTest(member=member):
                payload = _locator_payload(package_index_member_identity=member)
                self.assertEqual(
                    contract.parse_persisted_record(
                        _sealed_raw(payload, "locator_sha256"),
                        contract.LOCATOR_SCHEMA,
                    ).schema_version,
                    LOCATOR_SCHEMA_VERSION,
                )

    def test_approval_role_and_subject_relationship_attacks_reject(self) -> None:
        attacks = (
            {
                "approval_role": "locator_pin",
                "subject_role": "one_thesis_contract",
                "detached_message_domain": APPROVAL_DOMAINS["locator_pin"],
            },
            {
                "approval_role": "artifact_pin",
                "subject_role": "path_b_positive_intake_locator",
                "detached_message_domain": APPROVAL_DOMAINS["artifact_pin"],
            },
        )
        for index, attack in enumerate(attacks):
            with self.subTest(index=index):
                self._assert_rejected(
                    _approval_payload(**attack),
                    "approval_sha256",
                    "EXTERNAL_ROLE_APPROVAL_SCHEMA",
                )

    def test_generation_zero_result_rejects_input_refs_and_nonzero_counters(
        self,
    ) -> None:
        attacks = (
            {"input_refs": {"external_root": "ROOT_SENTINEL"}},
            {"input_refs": {"signing_key": "KEY_SENTINEL"}},
            {"input_counts": {"authenticated_locator_count": 1}},
            {"input_counts": {"task6_vnext_authority_count": 1}},
            {"stage_counters": {"candidate_path_construction_count": 1}},
            {"stage_counters": {"member_read_count": 1}},
            {"stage_counters": {"source_read_count": 1}},
            {"stage_counters": {"output_write_count": 1}},
        )
        for index, attack in enumerate(attacks):
            with self.subTest(index=index):
                self._assert_rejected(
                    _result_payload(**attack),
                    "result_sha256",
                    "RESULT_SCHEMA",
                )

    def test_replay_rollback_branch_and_rotation_metadata_never_bootstraps(
        self,
    ) -> None:
        contract = _contract()
        orchestrator = importlib.import_module("iclr2027.path_b_positive_intake")
        structural_attacks = (
            _locator_payload(
                locator_logical_id="locator:replay",
                package_generation=7,
                predecessor_locator_sha256=_digest(600),
            ),
            _locator_payload(
                locator_logical_id="locator:rollback",
                package_generation=6,
                predecessor_locator_sha256=_digest(599),
                rotation_current_head_sha256=_digest(700),
            ),
            _locator_payload(
                locator_logical_id="locator:branch",
                package_generation=7,
                predecessor_locator_sha256=_digest(600),
                verifier_challenge_sha256=_digest(701),
            ),
            _locator_payload(
                predecessor_locator_sha256=HEX_B,
                rotation_current_head_sha256=HEX_B,
                verifier_challenge_sha256=HEX_B,
            ),
        )
        baseline = orchestrator.current_status().to_dict()
        for index, payload in enumerate(structural_attacks):
            with self.subTest(index=index):
                record = contract.parse_persisted_record(
                    _sealed_raw(payload, "locator_sha256"),
                    contract.LOCATOR_SCHEMA,
                )
                with self.assertRaisesRegex(
                    orchestrator.NeedsContextError,
                    "^external_root_missing$",
                ):
                    orchestrator.validate_authenticated_path_b_intake(record)
                self.assertEqual(orchestrator.current_status().to_dict(), baseline)
                self.assertEqual(baseline["operation_count"], 0)
                self.assertEqual(baseline["authenticated_locator_count"], 0)
                self.assertEqual(baseline["authenticated_package_count"], 0)

    def test_required_pin_inventory_reference_bijection_is_accepted(self) -> None:
        contract = _contract()
        payload = _index_payload_with_pin_inventory()
        try:
            record = contract.parse_persisted_record(
                _sealed_raw(payload, "index_sha256"),
                contract.PACKAGE_INDEX_SCHEMA,
            )
        except contract.IntakeContractError as error:
            self.fail(f"required pin inventory/reference equality rejected: {error}")
        self.assertEqual(record.schema_version, INDEX_SCHEMA_VERSION)

    def test_index_inventory_kinds_role_coverage_and_pin_matches_are_closed(
        self,
    ) -> None:
        no_pin_inventory = _index_payload()
        no_pin_inventory["referenced_members"] = [
            item
            for item in no_pin_inventory["referenced_members"]
            if item["member_kind"] != "pin_approval"
        ]

        duplicate_roles = [dict(item) for item in no_pin_inventory["pin_approval_refs"]]
        duplicate_roles[1]["subject_role"] = duplicate_roles[0]["subject_role"]

        unknown_kind = [dict(item) for item in _index_payload()["referenced_members"]]
        unknown_kind[0]["member_kind"] = "caller_minted_member_kind"

        extra_unmatched_pin = [
            dict(item) for item in _index_payload()["referenced_members"]
        ]
        extra_unmatched_pin.append(
            {
                "member_kind": "pin_approval",
                "member_identity": "approvals/unmatched.json",
                "file_byte_count": 4100,
                "file_sha256": _digest(4100),
            }
        )

        attacks = (
            ("zero_pin_match", no_pin_inventory),
            (
                "duplicate_role_coverage",
                _index_payload(pin_approval_refs=duplicate_roles),
            ),
            ("unknown_member_kind", _index_payload(referenced_members=unknown_kind)),
            (
                "extra_unmatched_pin_inventory",
                _index_payload(referenced_members=extra_unmatched_pin),
            ),
        )
        for family, payload in attacks:
            with self.subTest(family=family):
                self._assert_rejected(
                    payload,
                    "index_sha256",
                    "PACKAGE_INDEX_SCHEMA",
                )

        multiply_matched = _index_payload_with_pin_inventory()
        first_pin_member = next(
            item
            for item in multiply_matched["referenced_members"]
            if item["member_kind"] == "pin_approval"
        )
        multiply_matched["referenced_members"].append(dict(first_pin_member))
        with self.subTest(family="multiple_pin_match"):
            self._assert_rejected(
                multiply_matched,
                "index_sha256",
                "PACKAGE_INDEX_SCHEMA",
            )

    def test_core_triple_roles_are_the_exact_ordered_seven_role_census(self) -> None:
        for index in range(len(CORE_ROLES)):
            core = [dict(item) for item in _index_payload()["core_triples"]]
            core[index]["role"] = "caller_minted_role"
            with self.subTest(family="unknown", index=index):
                self._assert_rejected(
                    _index_payload(core_triples=core),
                    "index_sha256",
                    "PACKAGE_INDEX_SCHEMA",
                )

        swapped = [dict(item) for item in _index_payload()["core_triples"]]
        swapped[0]["role"], swapped[1]["role"] = (
            swapped[1]["role"],
            swapped[0]["role"],
        )
        duplicate = [dict(item) for item in _index_payload()["core_triples"]]
        duplicate[1]["role"] = duplicate[0]["role"]
        for family, core in (("reordered", swapped), ("duplicate", duplicate)):
            with self.subTest(family=family):
                self._assert_rejected(
                    _index_payload(core_triples=core),
                    "index_sha256",
                    "PACKAGE_INDEX_SCHEMA",
                )

    def test_approval_timestamp_is_exact_canonical_utc(self) -> None:
        for value in (
            "tomorrow",
            "2026-02-30T00:00:00Z",
            "2026-08-30T00:00:00+00:00",
        ):
            with self.subTest(value=value):
                self._assert_rejected(
                    _approval_payload(approved_at_utc=value),
                    "approval_sha256",
                    "EXTERNAL_ROLE_APPROVAL_SCHEMA",
                )

    def test_member_identities_reject_windows_illegal_characters_everywhere(
        self,
    ) -> None:
        for character in '<>"|?*':
            core_fields = (
                "artifact_member_identity",
                "envelope_member_identity",
                "pin_member_identity",
            )
            for field in core_fields:
                core = [dict(item) for item in _index_payload()["core_triples"]]
                core[0][field] = f"core/illegal{character}name.json"
                with self.subTest(character=character, location=field):
                    self._assert_rejected(
                        _index_payload(core_triples=core),
                        "index_sha256",
                        "PACKAGE_INDEX_SCHEMA",
                    )

            members = [dict(item) for item in _index_payload()["referenced_members"]]
            members[0]["member_identity"] = f"members/illegal{character}name.json"
            with self.subTest(character=character, location="referenced_member"):
                self._assert_rejected(
                    _index_payload(referenced_members=members),
                    "index_sha256",
                    "PACKAGE_INDEX_SCHEMA",
                )

            pin_refs = [dict(item) for item in _index_payload()["pin_approval_refs"]]
            pin_refs[0]["approval_member_identity"] = (
                f"approvals/illegal{character}name.json"
            )
            matching_members = [
                dict(item) for item in _index_payload()["referenced_members"]
            ]
            matching_pin = next(
                item
                for item in matching_members
                if item["member_kind"] == "pin_approval"
                and item["member_identity"]
                == _index_payload()["pin_approval_refs"][0]["approval_member_identity"]
            )
            matching_pin["member_identity"] = pin_refs[0]["approval_member_identity"]
            with self.subTest(character=character, location="pin_approval_ref"):
                self._assert_rejected(
                    _index_payload(
                        pin_approval_refs=pin_refs,
                        referenced_members=matching_members,
                    ),
                    "index_sha256",
                    "PACKAGE_INDEX_SCHEMA",
                )

            for field in (
                "signing_public_key_member_identity",
                "detached_signature_member_identity",
            ):
                with self.subTest(character=character, location=field):
                    self._assert_rejected(
                        _approval_payload(**{field: f"members/illegal{character}name"}),
                        "approval_sha256",
                        "EXTERNAL_ROLE_APPROVAL_SCHEMA",
                    )

    def test_structural_self_hashed_record_parser_is_public(self) -> None:
        contract = _contract()
        self.assertTrue(
            callable(getattr(contract, "parse_self_hashed_record", None)),
            "missing structural self-hashed record parser",
        )

    def test_structural_self_hashed_record_parser_accepts_exact_canonical_bytes(
        self,
    ) -> None:
        contract = _contract()
        payload = {
            "record_version": 1,
            "schema_version": "ace.iclr2027.structural_test.v1",
        }
        raw = _sealed_raw(payload, "record_sha256")
        try:
            record = contract.parse_self_hashed_record(
                raw,
                "ace.iclr2027.structural_test.v1",
                "record_sha256",
            )
        except contract.IntakeContractError as error:
            self.fail(f"exact structural record rejected: {error}")
        self.assertEqual(record.raw_bytes, raw)
        self.assertEqual(record.canonical_body, raw[:-1])
        self.assertEqual(record.file_sha256, sha256(raw).hexdigest())
        self.assertEqual(
            record.self_sha256,
            sha256(_canonical(payload)).hexdigest(),
        )

    def test_structural_self_hashed_record_parser_rejects_boundary_attacks(
        self,
    ) -> None:
        contract = _contract()
        schema = "ace.iclr2027.structural_test.v1"
        payload = {"record_version": 1, "schema_version": schema}
        raw = _sealed_raw(payload, "record_sha256")
        body = json.loads(raw[:-1])
        stale_hash_body = dict(body)
        stale_hash_body["record_version"] = 2
        attacks = (
            ("nonbytes", "not-bytes", schema, "record_sha256"),
            ("missing_lf", raw[:-1], schema, "record_sha256"),
            ("extra_lf", raw + b"\n", schema, "record_sha256"),
            ("crlf", raw[:-1] + b"\r\n", schema, "record_sha256"),
            (
                "wrong_schema_body",
                _sealed_raw(
                    {
                        "record_version": 1,
                        "schema_version": "ace.iclr2027.other.v1",
                    },
                    "record_sha256",
                ),
                schema,
                "record_sha256",
            ),
            ("wrong_expected_schema", raw, "ace.iclr2027.other.v1", "record_sha256"),
            ("empty_expected_schema", raw, "", "record_sha256"),
            ("wrong_self_field", raw, schema, "other_sha256"),
            ("empty_self_field", raw, schema, ""),
            (
                "missing_self_field",
                _canonical(payload) + b"\n",
                schema,
                "record_sha256",
            ),
            (
                "wrong_self_hash",
                _canonical({**payload, "record_sha256": "f" * 64}) + b"\n",
                schema,
                "record_sha256",
            ),
            (
                "body_drift_stale_hash",
                _canonical(stale_hash_body) + b"\n",
                schema,
                "record_sha256",
            ),
            (
                "noncanonical_whitespace",
                b'{"record_sha256":"'
                + body["record_sha256"].encode("ascii")
                + b'", "record_version":1,"schema_version":"'
                + schema.encode("ascii")
                + b'"}\n',
                schema,
                "record_sha256",
            ),
            (
                "duplicate_key",
                b'{"record_sha256":"'
                + body["record_sha256"].encode("ascii")
                + b'","record_version":1,"record_version":1,"schema_version":"'
                + schema.encode("ascii")
                + b'"}\n',
                schema,
                "record_sha256",
            ),
        )
        for family, attacked_raw, expected_schema, self_field in attacks:
            with self.subTest(family=family):
                with self.assertRaises(contract.IntakeContractError):
                    contract.parse_self_hashed_record(
                        attacked_raw,
                        expected_schema,
                        self_field,
                    )

    def test_structural_parser_owns_utf8_and_sorted_key_canonicalization(
        self,
    ) -> None:
        contract = _contract()
        schema = "ace.iclr2027.structural_test.v1"
        literal_utf8 = _sealed_raw(
            {"fixture": "caf\u00e9", "schema_version": schema},
            "record_sha256",
        )
        try:
            contract.parse_self_hashed_record(
                literal_utf8,
                schema,
                "record_sha256",
            )
        except contract.IntakeContractError as error:
            self.fail(f"literal UTF-8 canonical record rejected: {error}")

        escaped_payload = {"fixture": "caf\u00e9", "schema_version": schema}
        escaped_body = json.dumps(
            escaped_payload,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        escaped_sealed = dict(escaped_payload)
        escaped_sealed["record_sha256"] = sha256(escaped_body).hexdigest()
        escaped = (
            json.dumps(
                escaped_sealed,
                ensure_ascii=True,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
        with self.assertRaises(contract.IntakeContractError):
            contract.parse_self_hashed_record(escaped, schema, "record_sha256")

        unsorted_body = (
            b'{"schema_version":"' + schema.encode("ascii") + b'","fixture":"x"}'
        )
        unsorted_self_hash = sha256(unsorted_body).hexdigest().encode("ascii")
        unsorted_raw = (
            b'{"schema_version":"'
            + schema.encode("ascii")
            + b'","fixture":"x","record_sha256":"'
            + unsorted_self_hash
            + b'"}\n'
        )
        with self.assertRaises(contract.IntakeContractError):
            contract.parse_self_hashed_record(
                unsorted_raw,
                schema,
                "record_sha256",
            )

    def test_ast_oracle_owns_canonical_json_serializer_keywords(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        mutations = (
            source.replace("ensure_ascii=False", "ensure_ascii=True", 1),
            source.replace("sort_keys=True", "sort_keys=False", 1),
        )
        for family, mutant in zip(
            ("ensure_ascii", "sort_keys"), mutations, strict=True
        ):
            with self.subTest(family=family):
                self.assertIn(
                    "canonical-json-keyword-drift",
                    _ast_capability_violations(mutant),
                )


if __name__ == "__main__":
    unittest.main()
