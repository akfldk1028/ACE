from __future__ import annotations

import ast
import importlib
import importlib.metadata
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "iclr2027" / "path_b_positive_intake_crypto.py"

ROLE_DOMAINS = {
    "legacy_search_impossibility_declaration": (
        "ACE-ICLR2027-LEGACY-SEARCH-IMPOSSIBILITY-VNEXT\x00"
    ),
    "one_thesis_contract": "ACE-ICLR2027-ONE-THESIS-CONTRACT-VNEXT\x00",
    "new_upstream_scientific_snapshot": (
        "ACE-ICLR2027-NEW-UPSTREAM-SCIENTIFIC-SNAPSHOT-VNEXT\x00"
    ),
    "independent_science_migration_review": (
        "ACE-ICLR2027-INDEPENDENT-SCIENCE-MIGRATION-REVIEW-VNEXT\x00"
    ),
    "independent_provenance_migration_review": (
        "ACE-ICLR2027-INDEPENDENT-PROVENANCE-MIGRATION-REVIEW-VNEXT\x00"
    ),
    "independent_security_migration_review": (
        "ACE-ICLR2027-INDEPENDENT-SECURITY-MIGRATION-REVIEW-VNEXT\x00"
    ),
    "provenance_migration_receipt": (
        "ACE-ICLR2027-PROVENANCE-MIGRATION-RECEIPT-VNEXT\x00"
    ),
}

# RFC 8032 section 7.1, TEST 1. Only the published public material is retained.
RFC8032_TEST1_PUBLIC_KEY = bytes.fromhex(
    "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
)
RFC8032_TEST1_MESSAGE = bytes.fromhex("")
RFC8032_TEST1_SIGNATURE = bytes.fromhex(
    "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155"
    "5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"
)

# RFC 8032 section 7.1, TEST 2. This second vector catches empty-message special cases.
RFC8032_TEST2_PUBLIC_KEY = bytes.fromhex(
    "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c"
)
RFC8032_TEST2_MESSAGE = bytes.fromhex("72")
RFC8032_TEST2_SIGNATURE = bytes.fromhex(
    "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da"
    "085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"
)

# Ed25519 subgroup order L encoded as a 32-byte little-endian scalar. S == L is
# noncanonical; it is not computed with, or sourced from, production code.
NONCANONICAL_S = bytes.fromhex(
    "edd3f55c1a631258d69cf7a2def9de1400000000000000000000000000000010"
)

IDENTITY_POINT = bytes.fromhex("01" + "00" * 31)
CANONICAL_SMALL_ORDER_POINTS = (
    bytes.fromhex("00" * 32),
    IDENTITY_POINT,
    bytes.fromhex("00" * 31 + "80"),
    bytes.fromhex("ec" + "ff" * 30 + "7f"),
    bytes.fromhex("26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc05"),
    bytes.fromhex("26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc85"),
    bytes.fromhex("c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac037a"),
    bytes.fromhex("c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac03fa"),
)
NONCANONICAL_POINT_ENCODINGS = (
    bytes.fromhex("ed" + "ff" * 30 + "7f"),
    bytes.fromhex("ee" + "ff" * 30 + "7f"),
    bytes.fromhex("01" + "00" * 30 + "80"),
)
CANONICAL_OFF_CURVE_POINT = bytes.fromhex("02" + "00" * 31)


class _BytesSubclass(bytes):
    pass


class _HostileLengthObserver:
    def __init__(self) -> None:
        self.observed = False

    def __len__(self) -> int:
        self.observed = True
        raise AssertionError("hostile __len__ was observed")


def _crypto():
    try:
        return importlib.import_module("iclr2027.path_b_positive_intake_crypto")
    except ModuleNotFoundError as error:
        raise AssertionError("production crypto module is absent") from error


def _crypto_ast_boundary_violations(source: str) -> tuple[str, ...]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ("syntax-error",)
    expected_imports = (
        "from cryptography.exceptions import InvalidSignature",
        (
            "from cryptography.hazmat.primitives.asymmetric.ed25519 import "
            "Ed25519PublicKey"
        ),
    )
    observed_imports = tuple(
        ast.unparse(node)
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
    )
    allowed_calls = {
        "Ed25519PublicKey.from_public_bytes",
        "Ed25519PublicKey.from_public_bytes(public_key).verify",
        "IntakeCryptoError",
        "_ROLE_DOMAINS[role].encode",
        "_decode_ed25519_point",
        "_double_ed25519_point",
        "_is_canonical_nonsmall_order_point",
        "artifact_bytes.endswith",
        "int.from_bytes",
        "len",
        "pow",
        "range",
        "type",
    }
    violations: list[str] = []
    if observed_imports != expected_imports:
        violations.append("import-drift")
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
    if public_classes != ("IntakeCryptoError",):
        violations.append("public-class-drift")
    if public_functions != ("artifact_signature_message", "verify_ed25519"):
        violations.append("public-function-drift")
    top_level_assignments = tuple(
        target.id
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (node.targets if isinstance(node, ast.Assign) else (node.target,))
        if isinstance(target, ast.Name)
    )
    if top_level_assignments != (
        "_ROLE_DOMAINS",
        "_FIELD_PRIME",
        "_CURVE_D",
        "_SQRT_MINUS_ONE",
        "_SUBGROUP_ORDER",
    ):
        violations.append("module-assignment-drift")
    trusted_names = {
        "Ed25519PublicKey",
        "IntakeCryptoError",
        "artifact_signature_message",
        "verify_ed25519",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and ast.unparse(node.func) not in allowed_calls:
            violations.append(f"operation-drift:{ast.unparse(node.func)}")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            violations.append(f"dunder-attribute-drift:{node.attr}")
        if (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Store)
            and node.id in trusted_names
        ):
            violations.append(f"trusted-name-rebound:{node.id}")
        if isinstance(node, ast.arg) and node.arg in trusted_names:
            violations.append(f"trusted-name-shadowed:{node.arg}")
    return tuple(violations)


class PositiveIntakeCryptoTests(unittest.TestCase):
    def _assert_crypto_failure(
        self,
        public_key: bytes,
        signature: bytes,
        message: bytes,
        *,
        reason: str = "cryptographic_signature_failed",
    ) -> None:
        module = _crypto()
        with self.assertRaises(module.IntakeCryptoError) as raised:
            module.verify_ed25519(public_key, signature, message)
        self.assertEqual(str(raised.exception), reason)

    def test_published_rfc8032_public_verification_known_answers(self) -> None:
        module = _crypto()
        vectors = (
            (
                RFC8032_TEST1_PUBLIC_KEY,
                RFC8032_TEST1_SIGNATURE,
                RFC8032_TEST1_MESSAGE,
            ),
            (
                RFC8032_TEST2_PUBLIC_KEY,
                RFC8032_TEST2_SIGNATURE,
                RFC8032_TEST2_MESSAGE,
            ),
        )
        for public_key, signature, message in vectors:
            with self.subTest(message_hex=message.hex()):
                self.assertIsNone(module.verify_ed25519(public_key, signature, message))

    def test_each_exact_role_builds_the_literal_domain_and_raw_artifact(self) -> None:
        module = _crypto()
        artifact = b'{"b":2,"a":1}\n'
        messages = []
        for role, domain in ROLE_DOMAINS.items():
            with self.subTest(role=role):
                expected = domain.encode("ascii") + artifact
                message = module.artifact_signature_message(role, artifact)
                self.assertEqual(message, expected)
                self.assertEqual(message.count(b"\x00"), 1)
                self.assertEqual(message.index(b"\x00"), len(domain) - 1)
                messages.append(message)
        self.assertEqual(len(set(messages)), len(ROLE_DOMAINS))

    def test_unknown_case_drift_and_raw_domain_as_role_are_rejected(self) -> None:
        module = _crypto()
        attacks = (
            "wrong_role",
            "One_Thesis_Contract",
            ROLE_DOMAINS["one_thesis_contract"],
        )
        for role in attacks:
            with self.subTest(role=role):
                with self.assertRaises(module.IntakeCryptoError) as raised:
                    module.artifact_signature_message(role, b"{}\n")
                self.assertEqual(str(raised.exception), "invalid_artifact_role")

    def test_artifact_must_be_exact_single_line_lf_terminated_bytes(self) -> None:
        module = _crypto()
        attacks = (
            b"",
            b"{}",
            b"{}\r\n",
            b"{}\n\n",
            b'{"a":\n1}\n',
            bytearray(b"{}\n"),
        )
        for artifact in attacks:
            with self.subTest(artifact=artifact):
                with self.assertRaises(module.IntakeCryptoError) as raised:
                    module.artifact_signature_message("one_thesis_contract", artifact)
                self.assertEqual(str(raised.exception), "invalid_artifact_bytes")

    def test_builder_preserves_signed_raw_json_instead_of_reserializing(self) -> None:
        module = _crypto()
        original = b'{"b":2,"a":1}\n'
        reserialized = b'{"a":1,"b":2}\n'
        original_message = module.artifact_signature_message(
            "one_thesis_contract", original
        )
        reserialized_message = module.artifact_signature_message(
            "one_thesis_contract", reserialized
        )
        self.assertTrue(original_message.endswith(original))
        self.assertNotEqual(original_message, reserialized_message)

    def test_wrong_role_lf_reserialization_and_cross_role_messages_are_distinct(
        self,
    ) -> None:
        module = _crypto()
        artifact = b'{"a":1,"b":2}\n'
        thesis = module.artifact_signature_message("one_thesis_contract", artifact)
        wrong_role = module.artifact_signature_message(
            "provenance_migration_receipt", artifact
        )
        reserialized = module.artifact_signature_message(
            "one_thesis_contract", b'{"b":2,"a":1}\n'
        )
        self.assertNotEqual(thesis, wrong_role)
        self.assertNotEqual(thesis, reserialized)
        self.assertNotEqual(thesis, thesis[:-1])

    def test_signature_public_key_and_message_bit_flips_fail_closed(self) -> None:
        public_key = bytearray(RFC8032_TEST2_PUBLIC_KEY)
        public_key[0] ^= 1
        signature = bytearray(RFC8032_TEST2_SIGNATURE)
        signature[-1] ^= 1
        message = bytearray(RFC8032_TEST2_MESSAGE)
        message[0] ^= 1
        attacks = (
            (bytes(public_key), RFC8032_TEST2_SIGNATURE, RFC8032_TEST2_MESSAGE),
            (RFC8032_TEST2_PUBLIC_KEY, bytes(signature), RFC8032_TEST2_MESSAGE),
            (RFC8032_TEST2_PUBLIC_KEY, RFC8032_TEST2_SIGNATURE, bytes(message)),
        )
        for index, attacked in enumerate(attacks):
            with self.subTest(index=index):
                self._assert_crypto_failure(*attacked)

    def test_key_and_signature_lengths_are_exact(self) -> None:
        module = _crypto()
        attacks = (
            (RFC8032_TEST1_PUBLIC_KEY[:-1], RFC8032_TEST1_SIGNATURE),
            (RFC8032_TEST1_PUBLIC_KEY + b"\x00", RFC8032_TEST1_SIGNATURE),
            (RFC8032_TEST1_PUBLIC_KEY, RFC8032_TEST1_SIGNATURE[:-1]),
            (RFC8032_TEST1_PUBLIC_KEY, RFC8032_TEST1_SIGNATURE + b"\x00"),
        )
        for public_key, signature in attacks:
            with self.subTest(key_len=len(public_key), signature_len=len(signature)):
                with self.assertRaises(module.IntakeCryptoError) as raised:
                    module.verify_ed25519(public_key, signature, RFC8032_TEST1_MESSAGE)
                self.assertEqual(str(raised.exception), "invalid_ed25519_length")

    def test_all_zero_public_key_is_rejected(self) -> None:
        self._assert_crypto_failure(
            bytes(32),
            RFC8032_TEST1_SIGNATURE,
            RFC8032_TEST1_MESSAGE,
            reason="invalid_ed25519_point",
        )

    def test_noncanonical_signature_scalar_is_rejected(self) -> None:
        noncanonical = RFC8032_TEST1_SIGNATURE[:32] + NONCANONICAL_S
        self.assertEqual(len(noncanonical), 64)
        self._assert_crypto_failure(
            RFC8032_TEST1_PUBLIC_KEY,
            noncanonical,
            RFC8032_TEST1_MESSAGE,
            reason="invalid_ed25519_scalar",
        )

    def test_identity_key_identity_r_zero_s_universal_forgery_is_rejected(
        self,
    ) -> None:
        module = _crypto()
        forged_signature = IDENTITY_POINT + bytes(32)
        messages = (
            b"",
            b"x",
            b"arbitrary message",
            module.artifact_signature_message("one_thesis_contract", b"{}\n"),
        )
        for message in messages:
            with self.subTest(message=message):
                self._assert_crypto_failure(
                    IDENTITY_POINT,
                    forged_signature,
                    message,
                    reason="invalid_ed25519_point",
                )

    def test_every_canonical_small_order_public_key_and_r_is_rejected(self) -> None:
        for point in CANONICAL_SMALL_ORDER_POINTS:
            with self.subTest(position="public_key", point=point.hex()):
                self._assert_crypto_failure(
                    point,
                    RFC8032_TEST1_SIGNATURE,
                    RFC8032_TEST1_MESSAGE,
                    reason="invalid_ed25519_point",
                )
            with self.subTest(position="signature_r", point=point.hex()):
                self._assert_crypto_failure(
                    RFC8032_TEST1_PUBLIC_KEY,
                    point + bytes(32),
                    RFC8032_TEST1_MESSAGE,
                    reason="invalid_ed25519_point",
                )

    def test_noncanonical_public_key_and_r_encodings_are_rejected(self) -> None:
        for point in NONCANONICAL_POINT_ENCODINGS:
            with self.subTest(position="public_key", point=point.hex()):
                self._assert_crypto_failure(
                    point,
                    RFC8032_TEST2_SIGNATURE,
                    RFC8032_TEST2_MESSAGE,
                    reason="invalid_ed25519_point",
                )
            with self.subTest(position="signature_r", point=point.hex()):
                self._assert_crypto_failure(
                    RFC8032_TEST2_PUBLIC_KEY,
                    point + bytes(32),
                    RFC8032_TEST2_MESSAGE,
                    reason="invalid_ed25519_point",
                )

    def test_canonical_encoding_that_is_not_on_curve_is_rejected(self) -> None:
        self._assert_crypto_failure(
            CANONICAL_OFF_CURVE_POINT,
            RFC8032_TEST2_SIGNATURE,
            RFC8032_TEST2_MESSAGE,
            reason="invalid_ed25519_point",
        )
        self._assert_crypto_failure(
            RFC8032_TEST2_PUBLIC_KEY,
            CANONICAL_OFF_CURVE_POINT + bytes(32),
            RFC8032_TEST2_MESSAGE,
            reason="invalid_ed25519_point",
        )

    def test_every_signature_scalar_at_or_above_l_is_rejected(self) -> None:
        subgroup_order = int.from_bytes(NONCANONICAL_S, "little")
        valid_s = int.from_bytes(RFC8032_TEST2_SIGNATURE[32:], "little")
        scalars = (
            subgroup_order,
            subgroup_order + 1,
            valid_s + subgroup_order,
            (1 << 256) - 1,
        )
        for scalar in scalars:
            signature = RFC8032_TEST2_SIGNATURE[:32] + scalar.to_bytes(32, "little")
            with self.subTest(scalar=scalar):
                self._assert_crypto_failure(
                    RFC8032_TEST2_PUBLIC_KEY,
                    signature,
                    RFC8032_TEST2_MESSAGE,
                    reason="invalid_ed25519_scalar",
                )

    def test_verify_rejects_every_nonexact_bytes_type_before_observation(
        self,
    ) -> None:
        module = _crypto()
        valid = (
            RFC8032_TEST1_PUBLIC_KEY,
            RFC8032_TEST1_SIGNATURE,
            RFC8032_TEST1_MESSAGE,
        )
        for position, original in enumerate(valid):
            attacks = (
                None,
                "x" * len(original),
                bytearray(original),
                memoryview(original),
                _BytesSubclass(original),
                _HostileLengthObserver(),
            )
            for attacked in attacks:
                arguments = list(valid)
                arguments[position] = attacked
                with self.subTest(position=position, attacked_type=type(attacked)):
                    caught = None
                    try:
                        module.verify_ed25519(*arguments)
                    except Exception as error:
                        caught = error
                    self.assertIsInstance(caught, module.IntakeCryptoError)
                    self.assertEqual(str(caught), "invalid_ed25519_type")
                    if isinstance(attacked, _HostileLengthObserver):
                        self.assertFalse(attacked.observed)

    def test_valid_signature_cannot_be_reused_with_domain_lf_or_json_changes(
        self,
    ) -> None:
        attacks = (
            ROLE_DOMAINS["one_thesis_contract"].encode("ascii") + RFC8032_TEST2_MESSAGE,
            RFC8032_TEST2_MESSAGE + b"\n",
            b'{"a":1,"b":2}\n',
            ROLE_DOMAINS["provenance_migration_receipt"].encode("ascii")
            + RFC8032_TEST2_MESSAGE,
        )
        for message in attacks:
            with self.subTest(message=message):
                self._assert_crypto_failure(
                    RFC8032_TEST2_PUBLIC_KEY, RFC8032_TEST2_SIGNATURE, message
                )

    def test_pinned_public_dependency_is_the_observed_generation0_version(
        self,
    ) -> None:
        _crypto()
        self.assertEqual(importlib.metadata.version("cryptography"), "47.0.0")

    def test_module_ast_has_public_verification_only_and_no_capabilities(self) -> None:
        _crypto()
        tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
        allowed_import_roots = {"cryptography"}
        forbidden_names = {
            "Ed25519PrivateKey",
            "PrivateKey",
            "sign",
            "signing",
            "Path",
            "os",
            "subprocess",
            "socket",
            "urllib",
            "requests",
            "pickle",
            "marshal",
            "shelve",
            "importlib",
        }
        forbidden_calls = {
            "open",
            "compile",
            "eval",
            "exec",
            "input",
            "getattr",
            "setattr",
            "delattr",
            "hasattr",
            "__import__",
        }
        observed_imports = set()
        public_function_names = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = (
                    [alias.name for alias in node.names]
                    if isinstance(node, ast.Import)
                    else [node.module or ""]
                )
                observed_imports.update(name.split(".", 1)[0] for name in names)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_"):
                    public_function_names.add(node.name)
            if isinstance(node, ast.Name):
                self.assertNotIn(node.id, forbidden_names)
            if isinstance(node, ast.Attribute):
                self.assertNotIn(node.attr, forbidden_names)
                self.assertNotIn(
                    node.attr,
                    {"read_text", "read_bytes", "write_text", "write_bytes"},
                )
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, forbidden_calls)
        self.assertEqual(
            public_function_names,
            {"artifact_signature_message", "verify_ed25519"},
        )
        self.assertTrue(observed_imports <= allowed_import_roots)


class TaskSevenCryptoAdversarialTests(unittest.TestCase):
    def _assert_failure(
        self,
        public_key: bytes,
        signature: bytes,
        message: bytes,
        reason: str,
    ) -> None:
        module = _crypto()
        with self.assertRaises(module.IntakeCryptoError) as raised:
            module.verify_ed25519(public_key, signature, message)
        self.assertEqual(str(raised.exception), reason)

    def test_point_scalar_and_exact_type_attack_matrix(self) -> None:
        point_attacks = (
            (bytes(32), RFC8032_TEST1_SIGNATURE),
            (IDENTITY_POINT, RFC8032_TEST1_SIGNATURE),
            (NONCANONICAL_POINT_ENCODINGS[0], RFC8032_TEST1_SIGNATURE),
            (
                RFC8032_TEST1_PUBLIC_KEY,
                IDENTITY_POINT + RFC8032_TEST1_SIGNATURE[32:],
            ),
            (
                RFC8032_TEST1_PUBLIC_KEY,
                CANONICAL_OFF_CURVE_POINT + RFC8032_TEST1_SIGNATURE[32:],
            ),
        )
        for index, (public_key, signature) in enumerate(point_attacks):
            with self.subTest(family="point", index=index):
                self._assert_failure(
                    public_key,
                    signature,
                    RFC8032_TEST1_MESSAGE,
                    "invalid_ed25519_point",
                )

        subgroup_order = int.from_bytes(NONCANONICAL_S, "little")
        for scalar in (subgroup_order, subgroup_order + 1, (1 << 256) - 1):
            with self.subTest(family="scalar", scalar=scalar):
                self._assert_failure(
                    RFC8032_TEST2_PUBLIC_KEY,
                    RFC8032_TEST2_SIGNATURE[:32] + scalar.to_bytes(32, "little"),
                    RFC8032_TEST2_MESSAGE,
                    "invalid_ed25519_scalar",
                )

        module = _crypto()
        exact = (
            RFC8032_TEST2_PUBLIC_KEY,
            RFC8032_TEST2_SIGNATURE,
            RFC8032_TEST2_MESSAGE,
        )
        for position, value in enumerate(exact):
            arguments = list(exact)
            arguments[position] = _BytesSubclass(value)
            with self.subTest(family="exact_type", position=position):
                with self.assertRaisesRegex(
                    module.IntakeCryptoError,
                    "^invalid_ed25519_type$",
                ):
                    module.verify_ed25519(*arguments)

    def test_role_domain_nul_lf_reserialization_and_cross_role_replay_matrix(
        self,
    ) -> None:
        module = _crypto()
        artifact = b'{"a":1,"b":2}\n'
        messages = {
            role: module.artifact_signature_message(role, artifact)
            for role in ROLE_DOMAINS
        }
        self.assertEqual(len(messages), 7)
        self.assertEqual(len(set(messages.values())), 7)
        for role, message in messages.items():
            with self.subTest(role=role):
                expected = ROLE_DOMAINS[role].encode("ascii") + artifact
                self.assertEqual(message, expected)
                self.assertEqual(message.count(b"\x00"), 1)
                self.assertTrue(message.endswith(b"\n"))
                self.assertNotIn(b"\r", message)

        misuse_messages = (
            messages["one_thesis_contract"],
            messages["provenance_migration_receipt"],
            b'{"b":2,"a":1}\n',
            RFC8032_TEST2_MESSAGE + b"\n",
        )
        for index, message in enumerate(misuse_messages):
            with self.subTest(family="signature_replay", index=index):
                self._assert_failure(
                    RFC8032_TEST2_PUBLIC_KEY,
                    RFC8032_TEST2_SIGNATURE,
                    message,
                    "cryptographic_signature_failed",
                )

    def test_crypto_ast_boundary_rejects_private_and_capability_mutations(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertEqual(_crypto_ast_boundary_violations(source), ())
        mutations = (
            "import os",
            "open('KEY_SENTINEL')",
            "def sign(value):\n    return value",
            "def from_bytes(value):\n    return value",
            "Ed25519PublicKey = object",
            "_CAPABILITY = IntakeCryptoError.__mro__[1].__subclasses__",
            (
                "from cryptography.hazmat.primitives.asymmetric.ed25519 "
                "import Ed25519PrivateKey\nEd25519PrivateKey.generate()"
            ),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assertTrue(
                    _crypto_ast_boundary_violations(f"{source}\n{mutation}\n")
                )


if __name__ == "__main__":
    unittest.main()
