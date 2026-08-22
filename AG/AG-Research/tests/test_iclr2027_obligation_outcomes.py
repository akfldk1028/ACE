"""Synthetic-only contract tests for blind architectural branch outcomes."""

from __future__ import annotations

import ast
import base64
from dataclasses import FrozenInstanceError, fields
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from iclr2027 import obligation_outcomes as subject
from iclr2027.capability_binding import controller_catalog_bytes
from iclr2027.obligation_contract import ObligationState
from iclr2027.schema import ArchitecturePublicCase


SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64
PREFIX = "prefix:" + "1" * 64
SLOT = "slot:" + "2" * 64
PACKET = "packet:" + "3" * 64


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")


def _frame(payload: dict[str, object]) -> bytes:
    body = _canonical(payload)
    return len(body).to_bytes(8, "big") + body


def _unframe(frame: bytes) -> dict[str, object]:
    if len(frame) < 8:
        raise AssertionError("frame is shorter than its length prefix")
    size = int.from_bytes(frame[:8], "big")
    body = frame[8:]
    if size != len(body):
        raise AssertionError("frame length does not match its payload")
    value = json.loads(body)
    if type(value) is not dict:
        raise AssertionError("frame payload is not an object")
    if _canonical(value) != body:
        raise AssertionError("frame payload is not canonical JSON")
    return value


def _rehash_response(
    frame: bytes, **updates: object
) -> bytes:
    payload = _unframe(frame)
    payload.update(updates)
    payload.pop("response_sha256", None)
    payload["response_sha256"] = _sha(_canonical(payload))
    return _frame(payload)


def _reference_bytes(*, marker: str = "same") -> bytes:
    content = {
        "schema_version": "ace.iclr2027.blind_evaluator_reference.v1",
        "assessment_criteria": {"rubric": "synthetic-two-obligation"},
        "hidden_assessment_target": {"marker": marker},
    }
    return _canonical({**content, "content_sha256": _sha(_canonical(content))})


def _usage(*, signed_zero: float = 0.0) -> subject.CompleteUsageSummary:
    rows = (
        subject.CallClassUsage("agent", 2, 1, 30, 1.25, 0.30),
        subject.CallClassUsage("selector", 1, 0, 4, 0.25, 0.04),
        subject.CallClassUsage("router", 0, 0, 0, signed_zero, signed_zero),
        subject.CallClassUsage("verifier", 1, 0, 7, 0.50, 0.07),
        subject.CallClassUsage("synthesis", 1, 0, 9, 0.75, 0.09),
    )
    return subject.CompleteUsageSummary(rows, SHA_A)


def _spec() -> subject.EvaluationImplementationSpec:
    root = Path(__file__).resolve().parents[1]
    members = tuple(
        sorted(
            (
                (
                    "evaluate_iclr2027_obligation_branches.py",
                    _sha((root / "evaluate_iclr2027_obligation_branches.py").read_bytes()),
                ),
                (
                    "iclr2027/obligation_outcomes.py",
                    _sha(Path(subject.__file__).read_bytes()),
                ),
            ),
            key=lambda row: row[0].encode("utf-8"),
        )
    )
    return subject.EvaluationImplementationSpec._for_test(
        relative_path="synthetic/evaluation-spec.json",
        external_file_sha256=SHA_D,
        implementation_sha256s=members,
    )


def _evaluator() -> subject.BlindBranchEvaluator:
    return subject._Phase4ASyntheticBlindEvaluator()


def _key(
    treatment: str = "capability_packet",
    *,
    repeat: int = 0,
    seed: int = 7,
    slot: str | None = SLOT,
    packet: str | None = PACKET,
    action: str = "ASK_LAW",
) -> subject.BranchTreatmentKey:
    if treatment == "stop":
        slot, packet, action = None, None, "STOP"
    elif treatment == "solo_synthesis":
        slot, packet, action = None, None, "SOLO_SYNTHESIS"
    return subject.BranchTreatmentKey(
        "site01", "case01", PREFIX, treatment, slot, action, packet, repeat, seed
    )


def _provenance(
    key: subject.BranchTreatmentKey,
    pre: bytes,
    terminal: bytes,
    reference: bytes,
    *,
    spec: subject.EvaluationImplementationSpec | None = None,
) -> subject.OutcomeProvenance:
    packet_values = (SHA_B, SHA_C, SHA_D, SHA_A)
    if key.treatment_kind != "capability_packet":
        packet_values = (None, None, None, None)
    bound_spec = spec or _spec()
    return subject.OutcomeProvenance(
        source_receipt_sha256=SHA_A,
        branch_transaction_sha256=SHA_B,
        public_case_sha256=SHA_C,
        public_state_sha256=SHA_D,
        prefix_input_sha256=_sha(pre),
        pre_synthesis_output_sha256=_sha(pre),
        terminal_output_sha256=_sha(terminal),
        usage_ledger_sha256=SHA_A,
        evaluator_contract_sha256=SHA_B,
        evaluator_reference_sha256=_sha(reference),
        catalog_sha256=packet_values[0],
        crossover_plan_sha256=packet_values[1],
        execution_binding_sha256=packet_values[2],
        actual_packet_manifest_sha256=packet_values[3],
        assignment_receipt_sha256=SHA_C,
        evaluation_implementation_spec_sha256=bound_spec.spec_sha256,
    )


def _source(
    treatment: str = "capability_packet",
    *,
    repeat: int = 0,
    seed: int = 7,
    pre: bytes = b"one obligation closed",
    terminal: bytes = b"both obligations closed",
    reference: bytes | None = None,
) -> subject.BranchEvaluationSource:
    if treatment == "stop":
        terminal = pre
    key = _key(treatment, repeat=repeat, seed=seed)
    ref = reference or _reference_bytes()
    spec = _spec()
    return subject.BranchEvaluationSource(
        key=key,
        pre_synthesis_output=pre,
        terminal_output=terminal,
        evaluator_reference=ref,
        usage=_usage(),
        provenance=_provenance(key, pre, terminal, ref, spec=spec),
        implementation_spec=spec,
    )


class SyntheticBlindEvaluator:
    """Stateless test evaluator with a deliberately exact byte-only signature."""

    @property
    def contract_sha256(self) -> str:
        return SHA_B

    def evaluate(
        self,
        *,
        pre_synthesis_output: bytes,
        terminal_output: bytes,
        evaluator_reference: bytes,
    ) -> subject.BlindEvaluation:
        if not all(
            type(value) is bytes
            for value in (
                pre_synthesis_output,
                terminal_output,
                evaluator_reference,
            )
        ):
            raise AssertionError("the blind handoff must contain only exact bytes")
        stop = pre_synthesis_output == terminal_output
        closures = (
            subject.ObligationClosureOutcome("obligation:a", True, True),
            subject.ObligationClosureOutcome("obligation:b", False, not stop),
        )
        # Independent fixture arithmetic: 1/2 -> 2/2; F1({b1,b2},{b1})=2/3.
        return subject.BlindEvaluation(
            obligation_closures=closures,
            scores=subject.BlindOutcomeScores(
                0.5,
                0.5 if stop else 1.0,
                2.0 / 3.0,
                1.0,
                1.0,
                True,
                stop,
            ),
        )


class RaisingEvaluator(SyntheticBlindEvaluator):
    def evaluate(
        self,
        *,
        pre_synthesis_output: bytes,
        terminal_output: bytes,
        evaluator_reference: bytes,
    ) -> subject.BlindEvaluation:
        del pre_synthesis_output, terminal_output, evaluator_reference
        raise RuntimeError("synthetic scoring failure")


class AmbientFileEvaluator(SyntheticBlindEvaluator):
    def evaluate(
        self,
        *,
        pre_synthesis_output: bytes,
        terminal_output: bytes,
        evaluator_reference: bytes,
    ) -> subject.BlindEvaluation:
        del pre_synthesis_output, terminal_output, evaluator_reference
        open("forbidden", "rb")  # noqa: PTH123
        raise AssertionError("unreachable")


class StatefulEvaluator(SyntheticBlindEvaluator):
    def __init__(self) -> None:
        self.cached_outcome = object()


_PICKLE_EVENTS: list[str] = []
_PATH_ALIAS = Path
_SOCKET_ALIAS = socket.socket
_IMPORT_ALIAS = importlib.import_module
_HANDLE_ALIAS = sys.stdout
_TRANSITIVE_SECRET = "capability_packet"
_ENVIRONMENT_WAS_PRESENT_DURING_MODULE_IMPORT = bool(os.environ)


def _read_authorized_test_source_through_alias() -> bytes:
    return _PATH_ALIAS(__file__).read_bytes()


def _read_authorized_test_source_through_builtins() -> bytes:
    builtins_value = __builtins__
    opener = (
        builtins_value["open"]
        if type(builtins_value) is dict
        else builtins_value.open
    )
    with opener(__file__, "rb") as handle:
        return handle.read()


def _current_directory_through_helper() -> str:
    return os.getcwd()


def _make_transitive_closure(secret: str):
    def reveal() -> str:
        return secret

    return reveal


_TRANSITIVE_CLOSURE = _make_transitive_closure(_TRANSITIVE_SECRET)


def _hidden_callback_alias() -> bool:
    return True


_CALLABLE_ALIAS = _hidden_callback_alias
_PARENT_MAGIC_EVENTS: list[str] = []


class _ParentMagicGlobal:
    def __hash__(self) -> int:
        _PARENT_MAGIC_EVENTS.append("hash")
        return 1

    def __eq__(self, _other: object) -> bool:
        _PARENT_MAGIC_EVENTS.append("eq")
        return False


_PARENT_MAGIC_GLOBAL = _ParentMagicGlobal()
_UNHASHABLE_GLOBAL: list[str] = []


class ParentMagicGlobalEvaluator:
    __slots__ = ()

    @property
    def contract_sha256(self) -> str:
        return SHA_B

    def evaluate(
        self,
        *,
        pre_synthesis_output: bytes,
        terminal_output: bytes,
        evaluator_reference: bytes,
    ) -> subject.BlindEvaluation:
        del pre_synthesis_output, terminal_output, evaluator_reference
        if _PARENT_MAGIC_GLOBAL is None:
            raise AssertionError("unreachable")
        raise AssertionError("unreachable")


class UnhashableGlobalEvaluator:
    __slots__ = ()

    @property
    def contract_sha256(self) -> str:
        return SHA_B

    def evaluate(
        self,
        *,
        pre_synthesis_output: bytes,
        terminal_output: bytes,
        evaluator_reference: bytes,
    ) -> subject.BlindEvaluation:
        del pre_synthesis_output, terminal_output, evaluator_reference
        if _UNHASHABLE_GLOBAL is None:
            raise AssertionError("unreachable")
        raise AssertionError("unreachable")


class PickleObservableEvaluator(SyntheticBlindEvaluator):
    def __reduce__(self):
        _PICKLE_EVENTS.append("evaluator-object-pickled")
        return (PickleObservableEvaluator, ())


class GlobalPathAliasEvaluator(SyntheticBlindEvaluator):
    def evaluate(
        self,
        *,
        pre_synthesis_output: bytes,
        terminal_output: bytes,
        evaluator_reference: bytes,
    ) -> subject.BlindEvaluation:
        if not _read_authorized_test_source_through_alias():
            raise AssertionError("authorized test source unexpectedly empty")
        return SyntheticBlindEvaluator.evaluate(
            self,
            pre_synthesis_output=pre_synthesis_output,
            terminal_output=terminal_output,
            evaluator_reference=evaluator_reference,
        )


class BuiltinsAliasEvaluator(SyntheticBlindEvaluator):
    def evaluate(
        self,
        *,
        pre_synthesis_output: bytes,
        terminal_output: bytes,
        evaluator_reference: bytes,
    ) -> subject.BlindEvaluation:
        if not _read_authorized_test_source_through_builtins():
            raise AssertionError("authorized test source unexpectedly empty")
        return SyntheticBlindEvaluator.evaluate(
            self,
            pre_synthesis_output=pre_synthesis_output,
            terminal_output=terminal_output,
            evaluator_reference=evaluator_reference,
        )


class SocketAliasEvaluator(SyntheticBlindEvaluator):
    def evaluate(
        self,
        *,
        pre_synthesis_output: bytes,
        terminal_output: bytes,
        evaluator_reference: bytes,
    ) -> subject.BlindEvaluation:
        handle = _SOCKET_ALIAS()
        handle.close()
        return SyntheticBlindEvaluator.evaluate(
            self,
            pre_synthesis_output=pre_synthesis_output,
            terminal_output=terminal_output,
            evaluator_reference=evaluator_reference,
        )


class ImportAndCwdAliasEvaluator(SyntheticBlindEvaluator):
    def evaluate(
        self,
        *,
        pre_synthesis_output: bytes,
        terminal_output: bytes,
        evaluator_reference: bytes,
    ) -> subject.BlindEvaluation:
        _IMPORT_ALIAS("pathlib")
        if not _current_directory_through_helper():
            raise AssertionError("child cwd unexpectedly empty")
        return SyntheticBlindEvaluator.evaluate(
            self,
            pre_synthesis_output=pre_synthesis_output,
            terminal_output=terminal_output,
            evaluator_reference=evaluator_reference,
        )


class ImportTimeEnvironmentAliasEvaluator(SyntheticBlindEvaluator):
    def evaluate(
        self,
        *,
        pre_synthesis_output: bytes,
        terminal_output: bytes,
        evaluator_reference: bytes,
    ) -> subject.BlindEvaluation:
        if not _ENVIRONMENT_WAS_PRESENT_DURING_MODULE_IMPORT:
            raise AssertionError("environment was unexpectedly absent at module import")
        return SyntheticBlindEvaluator.evaluate(
            self,
            pre_synthesis_output=pre_synthesis_output,
            terminal_output=terminal_output,
            evaluator_reference=evaluator_reference,
        )


class TransitiveClosureEvaluator(SyntheticBlindEvaluator):
    def evaluate(
        self,
        *,
        pre_synthesis_output: bytes,
        terminal_output: bytes,
        evaluator_reference: bytes,
    ) -> subject.BlindEvaluation:
        if _TRANSITIVE_CLOSURE() != _TRANSITIVE_SECRET:
            raise AssertionError("captured global changed")
        return SyntheticBlindEvaluator.evaluate(
            self,
            pre_synthesis_output=pre_synthesis_output,
            terminal_output=terminal_output,
            evaluator_reference=evaluator_reference,
        )


class InheritedHandleAliasEvaluator(SyntheticBlindEvaluator):
    def evaluate(
        self,
        *,
        pre_synthesis_output: bytes,
        terminal_output: bytes,
        evaluator_reference: bytes,
    ) -> subject.BlindEvaluation:
        _HANDLE_ALIAS.fileno()
        return SyntheticBlindEvaluator.evaluate(
            self,
            pre_synthesis_output=pre_synthesis_output,
            terminal_output=terminal_output,
            evaluator_reference=evaluator_reference,
        )


class CallbackAliasEvaluator(SyntheticBlindEvaluator):
    def evaluate(
        self,
        *,
        pre_synthesis_output: bytes,
        terminal_output: bytes,
        evaluator_reference: bytes,
    ) -> subject.BlindEvaluation:
        if not _CALLABLE_ALIAS():
            raise AssertionError("callback alias unexpectedly false")
        return SyntheticBlindEvaluator.evaluate(
            self,
            pre_synthesis_output=pre_synthesis_output,
            terminal_output=terminal_output,
            evaluator_reference=evaluator_reference,
        )


# Test methods below use only the one reviewed Phase 4A executable fixture.
# The adversarial classes above retain the local base captured at definition time
# and are supplied only to the private static-auditor seam.
SyntheticBlindEvaluator = getattr(
    subject, "_Phase4ASyntheticBlindEvaluator", SyntheticBlindEvaluator
)


class OutcomeContractTests(unittest.TestCase):
    def test_exact_exports_and_frozen_vocabularies(self) -> None:
        self.assertEqual(
            subject.__all__,
            (
                "BRANCH_OUTCOME_SCHEMA",
                "CALL_CLASS_ORDER",
                "TREATMENT_KINDS",
                "BranchOutcomeContractError",
                "BranchTreatmentKey",
                "ObligationClosureOutcome",
                "BlindOutcomeScores",
                "CallClassUsage",
                "CompleteUsageSummary",
                "OutcomeProvenance",
                "EvaluationImplementationSpec",
                "BranchOutcome",
                "BranchOutcomeReceipt",
                "BlindEvaluation",
                "BlindBranchEvaluator",
                "BranchEvaluationSource",
                "evaluate_branch_source",
                "build_branch_outcome_receipt",
                "verify_branch_outcomes_from_source",
                "validate_branch_outcome_table",
            ),
        )
        self.assertEqual(subject.BRANCH_OUTCOME_SCHEMA, "ace.iclr2027.branch_outcome.v1")
        self.assertEqual(
            subject.TREATMENT_KINDS,
            ("stop", "solo_synthesis", "capability_packet"),
        )
        self.assertEqual(
            subject.CALL_CLASS_ORDER,
            ("agent", "selector", "router", "verifier", "synthesis"),
        )
        self.assertTrue(issubclass(subject.BranchOutcomeContractError, ValueError))

    def test_all_records_are_frozen_slotted_and_recursive_values_are_tuples(self) -> None:
        persisted = (
            _key(),
            subject.ObligationClosureOutcome("obligation:a", True, False),
            subject.BlindOutcomeScores(0.5, 1.0, 2 / 3, 1.0, 1.0, True, False),
            _usage().by_call_class[0],
            _usage(),
            _source().provenance,
            _spec(),
            subject.evaluate_branch_source(_source(), SyntheticBlindEvaluator()),
        )
        receipt = subject.build_branch_outcome_receipt(
            (persisted[-1],), implementation_spec=_spec()
        )
        for record in (*persisted, receipt, subject.BlindEvaluation((), subject.BlindOutcomeScores(0.0, 0.0, 0.0, 0.0, 0.0, False, False)), _source()):
            with self.subTest(record=type(record).__name__):
                self.assertFalse(hasattr(record, "__dict__"))
                with self.assertRaises((FrozenInstanceError, AttributeError)):
                    setattr(record, fields(record)[0].name, None)
        self.assertIsInstance(_usage().by_call_class, tuple)

    def test_exact_nested_roundtrip_canonical_bytes_and_hashes(self) -> None:
        outcome = subject.evaluate_branch_source(_source(), SyntheticBlindEvaluator())
        for record in (
            outcome.key,
            outcome.obligation_closures[0],
            outcome.scores,
            outcome.usage.by_call_class[0],
            outcome.usage,
            outcome.provenance,
            outcome,
        ):
            with self.subTest(record=type(record).__name__):
                rebuilt = type(record).from_dict(record.to_dict())
                self.assertEqual(rebuilt, record)
                self.assertEqual(rebuilt.canonical_json(), record.canonical_json())
                self.assertNotIn("\n", record.canonical_json())
                self.assertEqual(rebuilt.sha256(), record.sha256())
        receipt = subject.build_branch_outcome_receipt((outcome,), implementation_spec=_spec())
        self.assertEqual(
            subject.BranchOutcomeReceipt.from_dict(receipt.to_dict()), receipt
        )

    def test_from_dict_rejects_extra_missing_keys_and_non_dicts(self) -> None:
        records = (
            (_key(), subject.BranchTreatmentKey),
            (subject.ObligationClosureOutcome("obligation:a", True, False), subject.ObligationClosureOutcome),
            (subject.BlindOutcomeScores(0.0, 1.0, 0.0, 1.0, 1.0, False, False), subject.BlindOutcomeScores),
            (_usage().by_call_class[0], subject.CallClassUsage),
            (_usage(), subject.CompleteUsageSummary),
            (_source().provenance, subject.OutcomeProvenance),
            (subject.evaluate_branch_source(_source(), SyntheticBlindEvaluator()), subject.BranchOutcome),
        )
        for record, cls in records:
            payload = record.to_dict()
            with self.subTest(cls=cls.__name__, kind="extra"):
                with self.assertRaises(subject.BranchOutcomeContractError):
                    cls.from_dict({**payload, "extra": None})
            with self.subTest(cls=cls.__name__, kind="missing"):
                reduced = dict(payload)
                reduced.pop(next(iter(reduced)))
                with self.assertRaises(subject.BranchOutcomeContractError):
                    cls.from_dict(reduced)
            with self.subTest(cls=cls.__name__, kind="mapping-subclass"):
                with self.assertRaises(TypeError):
                    cls.from_dict(type("ForeignDict", (dict,), {})(payload))

    def test_identifiers_hashes_actions_and_native_integer_boundaries(self) -> None:
        for bad in ("", " site", "site ", "si/te", "si\\te", "si\x00te"):
            with self.subTest(site=bad), self.assertRaises(subject.BranchOutcomeContractError):
                subject.BranchTreatmentKey(bad, "case", PREFIX, "stop", None, "STOP", None, 0, 0)
        for bad_prefix in ("prefix:" + "A" * 64, "prefix:" + "1" * 63, SHA_A):
            with self.subTest(prefix=bad_prefix), self.assertRaises(subject.BranchOutcomeContractError):
                subject.BranchTreatmentKey("site", "case", bad_prefix, "stop", None, "STOP", None, 0, 0)
        for repeat, seed in ((True, 0), (0, True), (-1, 0), (0, -1), (0, 2**63)):
            with self.subTest(repeat=repeat, seed=seed), self.assertRaises((TypeError, subject.BranchOutcomeContractError)):
                subject.BranchTreatmentKey("site", "case", PREFIX, "stop", None, "STOP", None, repeat, seed)

    def test_exact_stop_solo_and_four_packet_action_contracts(self) -> None:
        self.assertEqual(_key("stop").evaluator_action, "STOP")
        self.assertEqual(_key("solo_synthesis").evaluator_action, "SOLO_SYNTHESIS")
        for action in ("ASK_LAW", "ASK_PARKING", "ASK_PROGRAM", "ASK_GEOMETRY"):
            self.assertEqual(_key(action=action).evaluator_action, action)
        invalid = (
            ("stop", SLOT, "STOP", None),
            ("stop", None, "stop", None),
            ("solo_synthesis", None, "SOLO_SYNTHESIS", PACKET),
            ("capability_packet", None, "ASK_LAW", PACKET),
            ("capability_packet", SLOT, "STOP", PACKET),
            ("capability_packet", SLOT, "ASK_LAW", None),
        )
        for treatment, slot, action, packet in invalid:
            with self.subTest(treatment=treatment, action=action), self.assertRaises((TypeError, subject.BranchOutcomeContractError)):
                subject.BranchTreatmentKey(
                    "site01",
                    "case01",
                    PREFIX,
                    treatment,
                    slot,
                    action,
                    packet,
                    0,
                    7,
                )

    def test_numeric_fields_require_native_finite_float_and_normalize_signed_zero(self) -> None:
        args = [0.0, 1.0, 0.0, 1.0, 1.0, False, False]
        for bad in (0, True, math.nan, math.inf, -0.1, 1.1):
            mutated = list(args)
            mutated[0] = bad
            with self.subTest(value=bad), self.assertRaises((TypeError, subject.BranchOutcomeContractError)):
                subject.BlindOutcomeScores(*mutated)
        negative = subject.BlindOutcomeScores(-0.0, 0.0, -0.0, 0.0, 0.0, False, False)
        positive = subject.BlindOutcomeScores(0.0, 0.0, 0.0, 0.0, 0.0, False, False)
        self.assertEqual(negative.to_dict(), positive.to_dict())
        self.assertEqual(negative.canonical_json(), positive.canonical_json())
        self.assertEqual(negative.sha256(), positive.sha256())
        self.assertEqual(math.copysign(1.0, negative.pre_synthesis_closure_quality), 1.0)

    def test_complete_usage_has_five_classes_and_hand_derived_totals(self) -> None:
        usage = _usage()
        self.assertEqual(tuple(row.call_class for row in usage.by_call_class), subject.CALL_CLASS_ORDER)
        self.assertEqual(
            usage.to_dict()["totals"],
            {
                "call_count": 5,
                "failed_retry_count": 1,
                "processed_tokens": 50,
                "latency_seconds": 2.75,
                "frozen_list_price_cost": 0.5,
            },
        )
        self.assertEqual(usage.by_call_class[0].failed_retry_count, 1)

    def test_complete_usage_rejects_class_omission_extra_duplicate_order_and_bad_retry(self) -> None:
        rows = _usage().by_call_class
        bad_sets = (rows[:-1], rows + (rows[-1],), (rows[1], rows[0], *rows[2:]))
        for bad in bad_sets:
            with self.subTest(count=len(bad)), self.assertRaises(subject.BranchOutcomeContractError):
                subject.CompleteUsageSummary(bad, SHA_A)
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject.CallClassUsage("agent", 0, 1, 0, 0.0, 0.0)
        with self.assertRaises(TypeError):
            subject.CallClassUsage("agent", True, 0, 0, 0.0, 0.0)
        with self.assertRaises(TypeError):
            subject.CallClassUsage("agent", 0, 0, 0, 0, 0.0)

    def test_complete_usage_rejects_caller_authored_totals_and_signed_zero_divergence(self) -> None:
        payload = _usage().to_dict()
        payload["totals"]["processed_tokens"] += 1
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject.CompleteUsageSummary.from_dict(payload)
        self.assertEqual(_usage(signed_zero=-0.0).sha256(), _usage().sha256())

    def test_provenance_packet_nullability_and_lowercase_hashes(self) -> None:
        packet_source = _source()
        self.assertIsNotNone(packet_source.provenance.catalog_sha256)
        stop_source = _source("stop")
        self.assertIsNone(stop_source.provenance.catalog_sha256)
        payload = stop_source.provenance.to_dict()
        payload["source_receipt_sha256"] = SHA_A.upper()
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject.OutcomeProvenance.from_dict(payload)
        payload = stop_source.provenance.to_dict()
        payload["catalog_sha256"] = SHA_A
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject.BranchEvaluationSource(
                key=stop_source.key,
                pre_synthesis_output=stop_source.pre_synthesis_output,
                terminal_output=stop_source.terminal_output,
                evaluator_reference=stop_source.evaluator_reference,
                usage=stop_source.usage,
                provenance=subject.OutcomeProvenance.from_dict(payload),
                implementation_spec=stop_source.implementation_spec,
            )

    def test_test_only_implementation_spec_derives_closure_and_rejects_bad_paths(self) -> None:
        spec = _spec()
        self.assertTrue(spec.test_only)
        self.assertEqual(spec.evaluator_module, "iclr2027.obligation_outcomes")
        self.assertEqual(
            spec.evaluator_qualname, "_Phase4ASyntheticBlindEvaluator"
        )
        self.assertEqual(
            spec.evaluator_logical_path, "iclr2027/obligation_outcomes.py"
        )
        self.assertEqual(spec.evaluator_contract_sha256, SHA_B)
        self.assertEqual(spec.evaluator_constructor, "zero_arg_stateless")
        self.assertEqual(
            spec.evaluator_source_sha256,
            dict(spec.implementation_sha256s)[spec.evaluator_logical_path],
        )
        self.assertEqual(spec.source_closure_sha256, _sha(_canonical([list(row) for row in spec.implementation_sha256s])))
        self.assertFalse(hasattr(subject.EvaluationImplementationSpec, "from_dict"))
        bad_paths = (
            "/absolute.py",
            "C:/drive.py",
            "bad\\path.py",
            "a//b.py",
            "a/./b.py",
            "a/../b.py",
        )
        for bad in bad_paths:
            with self.subTest(path=bad), self.assertRaises(subject.BranchOutcomeContractError):
                subject.EvaluationImplementationSpec._for_test(
                    relative_path="synthetic/spec.json",
                    external_file_sha256=SHA_A,
                    implementation_sha256s=((bad, SHA_B),),
                )
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject.EvaluationImplementationSpec._for_test(
                relative_path="synthetic/spec.json",
                external_file_sha256=SHA_A,
                implementation_sha256s=(("A.py", SHA_B), ("a.py", SHA_C)),
            )

    def test_blind_evaluation_is_in_memory_only_and_closures_are_canonical(self) -> None:
        evaluation = subject.BlindEvaluation(
            (
                subject.ObligationClosureOutcome("obligation:a", True, True),
                subject.ObligationClosureOutcome("obligation:b", False, True),
            ),
            subject.BlindOutcomeScores(
                0.5, 1.0, 2.0 / 3.0, 1.0, 1.0, True, False
            ),
        )
        for name in ("from_dict", "to_dict", "canonical_json", "sha256"):
            self.assertFalse(hasattr(evaluation, name))
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject.BlindEvaluation(
                tuple(reversed(evaluation.obligation_closures)), evaluation.scores
            )

    def test_source_is_nonserializable_and_validates_stop_stage_hashes(self) -> None:
        source = _source("stop")
        for name in ("from_dict", "to_dict", "canonical_json", "sha256"):
            self.assertFalse(hasattr(source, name))
        key = _key("stop")
        ref = _reference_bytes()
        spec = _spec()
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject.BranchEvaluationSource(
                key, b"pre", b"different", ref, _usage(),
                _provenance(key, b"pre", b"different", ref, spec=spec), spec
            )

    def test_reference_schema_hash_and_forbidden_metadata_reject_before_scoring(self) -> None:
        raw = json.loads(_reference_bytes())
        raw["content_sha256"] = SHA_A
        bad_ref = _canonical(raw)
        key = _key()
        spec = _spec()
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject.BranchEvaluationSource(
                key, b"pre", b"terminal", bad_ref, _usage(),
                _provenance(key, b"pre", b"terminal", bad_ref, spec=spec), spec
            )
        content = {
            "schema_version": "ace.iclr2027.blind_evaluator_reference.v1",
            "assessment_criteria": {"policy": "forbidden"},
            "hidden_assessment_target": {},
        }
        forbidden_ref = _canonical({**content, "content_sha256": _sha(_canonical(content))})
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject.BranchEvaluationSource(
                key, b"pre", b"terminal", forbidden_ref, _usage(),
                _provenance(key, b"pre", b"terminal", forbidden_ref, spec=spec), spec
            )

    def test_nested_reference_nonfinite_numbers_reject_recursively(self) -> None:
        key = _key()
        spec = _spec()
        for value in (math.nan, math.inf, -math.inf):
            content = {
                "schema_version": "ace.iclr2027.blind_evaluator_reference.v1",
                "assessment_criteria": {"nested": [{"score": value}]},
                "hidden_assessment_target": {"marker": "synthetic"},
            }
            reference = _canonical(
                {**content, "content_sha256": _sha(_canonical(content))}
            )
            with self.subTest(value=value), self.assertRaises(
                subject.BranchOutcomeContractError
            ):
                subject.BranchEvaluationSource(
                    key,
                    b"pre",
                    b"terminal",
                    reference,
                    _usage(),
                    _provenance(
                        key, b"pre", b"terminal", reference, spec=spec
                    ),
                    spec,
                )

    def test_evaluator_receives_three_bytes_only_and_science_fixture_is_hand_derived(self) -> None:
        outcome = subject.evaluate_branch_source(_source(), _evaluator())
        self.assertEqual(
            tuple((row.pre_synthesis_closed, row.post_synthesis_closed) for row in outcome.obligation_closures),
            ((True, True), (False, True)),
        )
        self.assertEqual(outcome.scores.pre_synthesis_closure_quality, 1 / 2)
        self.assertEqual(outcome.scores.blind_terminal_closure_quality, 2 / 2)
        self.assertAlmostEqual(outcome.scores.blocking_issue_f1, 2 / 3)
        self.assertEqual(outcome.scores.missing_evidence_f1, 1.0)
        self.assertEqual(outcome.scores.decision_accuracy, 1.0)

    def test_evaluation_runs_in_new_process_and_rejects_ambient_or_stateful_evaluators(self) -> None:
        responses: list[bytes] = []

        def capture_response(frame: bytes) -> bytes:
            responses.append(frame)
            return frame

        parent_calls: list[str] = []
        target_code = subject._Phase4ASyntheticBlindEvaluator.evaluate.__code__

        def profile(frame, event, arg):
            del arg
            if event == "call" and frame.f_code is target_code:
                parent_calls.append("direct-evaluate")

        previous_profile = sys.getprofile()
        sys.setprofile(profile)
        try:
            evaluation, child_pid = subject._run_blind_worker_for_test(
                _source(), response_mutator=capture_response
            )
        finally:
            sys.setprofile(previous_profile)
        self.assertIs(type(evaluation), subject.BlindEvaluation)
        self.assertEqual(parent_calls, [])
        self.assertEqual(len(responses), 1)
        self.assertEqual(_unframe(responses[0])["worker_pid"], child_pid)
        self.assertNotEqual(child_pid, os.getpid())
        for evaluator_class in (AmbientFileEvaluator, StatefulEvaluator):
            with self.subTest(evaluator=evaluator_class.__name__), self.assertRaises(
                subject.BranchOutcomeContractError
            ):
                subject._audit_evaluator_class_for_test(evaluator_class)

    def test_sealed_child_handoff_never_pickles_the_evaluator_object(self) -> None:
        _PICKLE_EVENTS.clear()
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject._audit_evaluator_class_for_test(PickleObservableEvaluator)
        self.assertEqual(_PICKLE_EVENTS, [])

    def test_canonical_child_request_contains_only_three_payloads_contract_nonce(self) -> None:
        request_frames: list[bytes] = []
        subject._run_blind_worker_for_test(
            _source(), request_capture=request_frames
        )
        self.assertEqual(len(request_frames), 1)
        request = _unframe(request_frames[0])
        self.assertEqual(
            set(request),
            {
                "schema_version",
                "nonce",
                "evaluator_contract_sha256",
                "pre_synthesis_output_b64",
                "terminal_output_b64",
                "evaluator_reference_b64",
                "request_sha256",
            },
        )
        self.assertEqual(
            request["schema_version"], "ace.iclr2027.blind_worker_request.v1"
        )
        self.assertEqual(request["evaluator_contract_sha256"], SHA_B)
        self.assertEqual(
            base64.b64decode(request["pre_synthesis_output_b64"], validate=True),
            b"one obligation closed",
        )
        self.assertEqual(
            base64.b64decode(request["terminal_output_b64"], validate=True),
            b"both obligations closed",
        )
        self.assertEqual(
            base64.b64decode(request["evaluator_reference_b64"], validate=True),
            _reference_bytes(),
        )
        nonce = bytes.fromhex(request["nonce"])
        self.assertEqual(len(nonce), 32)
        unsigned = {key: value for key, value in request.items() if key != "request_sha256"}
        self.assertEqual(request["request_sha256"], _sha(_canonical(unsigned)))
        for key in (
            "pre_synthesis_output_b64",
            "terminal_output_b64",
            "evaluator_reference_b64",
        ):
            decoded = base64.b64decode(request[key], validate=True)
            self.assertEqual(request[key], base64.b64encode(decoded).decode("ascii"))

    def test_child_contract_change_after_parent_check_is_rejected(self) -> None:
        def switch_contract(frame: bytes) -> bytes:
            return _rehash_response(frame, evaluator_contract_sha256=SHA_C)

        with self.assertRaises(subject.BranchOutcomeContractError):
            subject._run_blind_worker_for_test(
                _source(), response_mutator=switch_contract
            )

    def test_tampered_worker_response_nonce_is_rejected(self) -> None:
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject._run_blind_worker_for_test(
                _source(),
                response_mutator=lambda frame: _rehash_response(
                    frame, nonce="00" * 32
                ),
            )

    def test_public_evaluation_ignores_mutable_legacy_test_hook_globals(self) -> None:
        captured: list[bytes] = []

        def forge_response(_frame: bytes) -> bytes:
            raise AssertionError("public evaluation consulted a mutable test hook")

        with patch.object(
            subject, "_TEST_REQUEST_CAPTURE", captured, create=True
        ), patch.object(
            subject, "_TEST_RESPONSE_MUTATOR", forge_response, create=True
        ):
            outcome = subject.evaluate_branch_source(_source(), _evaluator())
        self.assertEqual(captured, [])
        self.assertEqual(outcome.scores.blind_terminal_closure_quality, 1.0)

    def test_public_evaluation_uses_hash_bound_bootstrap_not_mutable_global(self) -> None:
        launched: list[tuple[str, ...]] = []
        real_popen = subprocess.Popen
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "hostile-bootstrap-ran"
            hostile = (
                "from pathlib import Path; "
                f"Path({str(marker)!r}).write_bytes(b'owned')"
            )

            def observing_popen(argv, **kwargs):
                launched.append(tuple(argv))
                return real_popen(argv, **kwargs)

            with patch.object(
                subject, "_BLIND_WORKER_BOOTSTRAP", hostile
            ), patch.object(subject.subprocess, "Popen", side_effect=observing_popen):
                outcome = subject.evaluate_branch_source(_source(), _evaluator())

            self.assertFalse(marker.exists())
        self.assertEqual(len(launched), 1)
        self.assertNotEqual(launched[0][5], hostile)
        self.assertEqual(
            _sha(launched[0][5].encode("utf-8")),
            "00e19b82e8713b0cef68d5edbfc824575321bd1b4fbf2cf00471225d2ccd6749",
        )
        self.assertEqual(outcome.scores.blind_terminal_closure_quality, 1.0)

    def test_evaluator_validation_never_invokes_instance_attribute_hooks(self) -> None:
        observer: list[str] = []

        def observed_getattribute(instance, name):
            observer.append(name)
            return object.__getattribute__(instance, name)

        with patch.object(
            subject._Phase4ASyntheticBlindEvaluator,
            "__getattribute__",
            observed_getattribute,
            create=True,
        ):
            with self.assertRaises(subject.BranchOutcomeContractError):
                subject.evaluate_branch_source(_source(), _evaluator())
        self.assertEqual(observer, [])

    def test_blind_worker_rejects_bootstrap_digest_mismatch_before_launch(self) -> None:
        launches: list[tuple[object, ...]] = []

        def observe_launch(*args, **kwargs):
            launches.append((args, kwargs))
            raise AssertionError("digest mismatch reached process launch")

        with self.assertRaises(subject.BranchOutcomeContractError):
            subject._run_blind_worker_for_test(
                _source(),
                popen_factory=observe_launch,
                bootstrap_source_for_test="raise SystemExit(99)",
            )
        self.assertEqual(launches, [])

    def test_worker_timeout_is_bounded_and_fails_closed(self) -> None:
        events: list[object] = []

        class TimeoutProcess:
            pid = 424242
            returncode = None

            def communicate(self, input=None, timeout=None):
                events.append(("communicate", input, timeout))
                raise subprocess.TimeoutExpired("blind-worker", timeout)

            def terminate(self):
                events.append("terminate")

            def wait(self, timeout=None):
                events.append(("wait", timeout))
                if timeout is not None:
                    raise subprocess.TimeoutExpired("blind-worker", timeout)
                self.returncode = -9
                return self.returncode

            def kill(self):
                events.append("kill")

        launch: dict[str, object] = {}

        def fake_popen(argv, **kwargs):
            launch.update(argv=argv, kwargs=kwargs)
            cwd = Path(kwargs["cwd"])
            self.assertTrue(cwd.is_dir())
            self.assertEqual(tuple(cwd.iterdir()), ())
            return TimeoutProcess()

        with self.assertRaises(subject.BranchOutcomeContractError):
            subject._run_blind_worker_for_test(
                _source(),
                popen_factory=fake_popen,
                timeout_seconds=0.05,
                kill_wait_seconds=0.01,
            )
        argv = launch["argv"]
        kwargs = launch["kwargs"]
        self.assertEqual(argv[:6], [str(Path(sys.executable).resolve()), "-I", "-S", "-B", "-c", subject._BLIND_WORKER_BOOTSTRAP])
        self.assertEqual(argv[7:], ["iclr2027.obligation_outcomes", "_Phase4ASyntheticBlindEvaluator", _spec().evaluator_source_sha256])
        expected_env = {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
        }
        if os.name == "nt":
            for name in ("SystemRoot", "WINDIR"):
                if name in os.environ:
                    expected_env[name] = os.environ[name]
        self.assertEqual(kwargs["env"], expected_env)
        self.assertTrue(kwargs["close_fds"])
        self.assertIs(kwargs["stdin"], subprocess.PIPE)
        self.assertIs(kwargs["stdout"], subprocess.PIPE)
        self.assertIs(kwargs["stderr"], subprocess.PIPE)
        self.assertEqual(events[1:], ["terminate", ("wait", 0.01), "kill", ("wait", None)])

    def test_worker_abnormal_exit_is_a_contract_error(self) -> None:
        class AbnormalProcess:
            pid = 424243
            returncode = 17

            def communicate(self, input=None, timeout=None):
                del input, timeout
                return b"", b""

        with self.assertRaises(subject.BranchOutcomeContractError):
            subject._run_blind_worker_for_test(
                _source(), popen_factory=lambda *args, **kwargs: AbnormalProcess()
            )

    def test_worker_communication_oserror_is_bounded_reaped_and_translated(self) -> None:
        events: list[object] = []

        class BrokenPipeProcess:
            pid = 424244
            returncode = None

            def communicate(self, input=None, timeout=None):
                events.append(("communicate", input, timeout))
                raise OSError("synthetic broken pipe")

            def terminate(self):
                events.append("terminate")

            def wait(self, timeout=None):
                events.append(("wait", timeout))
                if timeout is not None:
                    raise subprocess.TimeoutExpired("blind-worker", timeout)
                self.returncode = -9
                return self.returncode

            def kill(self):
                events.append("kill")

        with self.assertRaises(subject.BranchOutcomeContractError) as raised:
            subject._run_blind_worker_for_test(
                _source(),
                popen_factory=lambda *args, **kwargs: BrokenPipeProcess(),
                timeout_seconds=0.05,
                kill_wait_seconds=0.01,
            )
        self.assertIsInstance(raised.exception.__cause__, OSError)
        self.assertEqual(
            events[1:],
            ["terminate", ("wait", 0.01), "kill", ("wait", None)],
        )

    def test_oversized_worker_response_rejects_before_json_decode(self) -> None:
        source = _source()

        class OversizedResponseProcess:
            pid = 424245
            returncode = 0

            def communicate(self, input=None, timeout=None):
                del input, timeout
                body = b"{" * (subject._MAX_RESPONSE_BYTES + 1)
                return len(body).to_bytes(8, "big") + body, b""

        with patch.object(
            subject,
            "_decode_json_bytes",
            side_effect=AssertionError("oversized response reached JSON decoder"),
        ):
            with self.assertRaises(subject.BranchOutcomeContractError):
                subject._run_blind_worker_for_test(
                    source,
                    popen_factory=lambda *args, **kwargs: OversizedResponseProcess(),
                )

    def test_module_global_path_helper_cannot_open_a_file_during_scoring(self) -> None:
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject._audit_evaluator_class_for_test(GlobalPathAliasEvaluator)

    def test_builtins_alias_cannot_open_a_file_during_scoring(self) -> None:
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject._audit_evaluator_class_for_test(BuiltinsAliasEvaluator)

    def test_socket_constructor_alias_is_rejected_before_scoring(self) -> None:
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject._audit_evaluator_class_for_test(SocketAliasEvaluator)

    def test_import_and_cwd_helpers_are_rejected_before_scoring(self) -> None:
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject._audit_evaluator_class_for_test(ImportAndCwdAliasEvaluator)

    def test_import_time_environment_snapshot_is_rejected_before_scoring(self) -> None:
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject._audit_evaluator_class_for_test(
                ImportTimeEnvironmentAliasEvaluator
            )

    def test_transitive_closure_global_is_rejected_before_scoring(self) -> None:
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject._audit_evaluator_class_for_test(TransitiveClosureEvaluator)

    def test_inherited_handle_alias_is_rejected_before_scoring(self) -> None:
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject._audit_evaluator_class_for_test(InheritedHandleAliasEvaluator)

    def test_transitive_callback_alias_is_rejected_before_scoring(self) -> None:
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject._audit_evaluator_class_for_test(CallbackAliasEvaluator)

    def test_static_audit_never_executes_parent_global_magic_or_leaks_type_error(self) -> None:
        _PARENT_MAGIC_EVENTS.clear()
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject._audit_evaluator_class_for_test(ParentMagicGlobalEvaluator)
        self.assertEqual(_PARENT_MAGIC_EVENTS, [])
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject._audit_evaluator_class_for_test(UnhashableGlobalEvaluator)

    def test_evaluator_contract_and_exception_fail_before_metadata_join(self) -> None:
        class WrongContract(SyntheticBlindEvaluator):
            @property
            def contract_sha256(self) -> str:
                return SHA_C

        with self.assertRaises(subject.BranchOutcomeContractError):
            subject._audit_evaluator_class_for_test(WrongContract)
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject.evaluate_branch_source(
                _source(terminal=b"raise:synthetic-evaluation-error"), _evaluator()
            )

    def test_metadata_permutation_with_identical_blind_bytes_returns_identical_result(self) -> None:
        one = _source(repeat=0, seed=7)
        two = _source(repeat=1, seed=8)
        first = subject.evaluate_branch_source(one, SyntheticBlindEvaluator())
        second = subject.evaluate_branch_source(two, SyntheticBlindEvaluator())
        self.assertEqual(first.obligation_closures, second.obligation_closures)
        self.assertEqual(first.scores, second.scores)
        self.assertNotEqual(first.key, second.key)

    def test_unsafe_stop_is_descriptive_and_only_valid_for_stop(self) -> None:
        stop = subject.evaluate_branch_source(_source("stop"), _evaluator())
        self.assertTrue(stop.scores.unsafe_stop)
        source = _source()
        packet = subject.evaluate_branch_source(source, _evaluator())
        bad = subject.BlindEvaluation(
            packet.obligation_closures,
            subject.BlindOutcomeScores(0.5, 1.0, 2 / 3, 1.0, 1.0, True, True),
        )
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject._join_blind_evaluation_for_test(source, bad)

    def test_outcome_id_recomputation_rejects_tamper_and_forbidden_fields(self) -> None:
        outcome = subject.evaluate_branch_source(_source(), SyntheticBlindEvaluator())
        payload = outcome.to_dict()
        payload["outcome_id"] = "outcome:" + SHA_A
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject.BranchOutcome.from_dict(payload)
        for forbidden in ("next_prefix", "transition", "stitched", "imputed", "best", "max", "oracle", "alignment", "policy", "utility"):
            payload = outcome.to_dict()
            payload[forbidden] = "forbidden"
            with self.subTest(field=forbidden), self.assertRaises(subject.BranchOutcomeContractError):
                subject.BranchOutcome.from_dict(payload)

    def test_table_preserves_repeats_and_rejects_duplicates_and_wrong_order(self) -> None:
        outcomes = tuple(
            subject.evaluate_branch_source(_source(repeat=i, seed=7 + i), SyntheticBlindEvaluator())
            for i in range(2)
        )
        subject.validate_branch_outcome_table(outcomes)
        self.assertEqual(tuple(row.key.repeat_index for row in outcomes), (0, 1))
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject.validate_branch_outcome_table((outcomes[0], outcomes[0]))
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject.validate_branch_outcome_table(tuple(reversed(outcomes)))

    def test_table_requires_shared_assessment_reference_and_source_hashes(self) -> None:
        one = subject.evaluate_branch_source(_source(repeat=0), SyntheticBlindEvaluator())
        changed = _reference_bytes(marker="changed")
        two = subject.evaluate_branch_source(
            _source(repeat=1, seed=8, reference=changed), SyntheticBlindEvaluator()
        )
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject.validate_branch_outcome_table((one, two))

    def test_reference_parity_mismatch_rejects_before_evaluator_serialization(self) -> None:
        baseline_sources = (
            _source(repeat=0),
            _source(repeat=1, seed=8),
        )
        outcomes = tuple(
            subject.evaluate_branch_source(source, SyntheticBlindEvaluator())
            for source in baseline_sources
        )
        receipt = subject.build_branch_outcome_receipt(
            outcomes, implementation_spec=_spec()
        )
        mismatched_sources = (
            baseline_sources[0],
            _source(
                repeat=1,
                seed=8,
                reference=_reference_bytes(marker="treatment-varying"),
            ),
        )
        _PICKLE_EVENTS.clear()
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject.verify_branch_outcomes_from_source(
                outcomes,
                receipt,
                sources=mismatched_sources,
                evaluator=PickleObservableEvaluator(),
            )
        self.assertEqual(_PICKLE_EVENTS, [])

    def test_reference_parity_preflight_emits_zero_canonical_worker_requests(self) -> None:
        baseline_sources = (
            _source(repeat=0),
            _source(repeat=1, seed=8),
        )
        outcomes = tuple(
            subject.evaluate_branch_source(source, SyntheticBlindEvaluator())
            for source in baseline_sources
        )
        receipt = subject.build_branch_outcome_receipt(
            outcomes, implementation_spec=_spec()
        )
        mismatched_sources = (
            baseline_sources[0],
            _source(
                repeat=1,
                seed=8,
                reference=_reference_bytes(marker="treatment-varying"),
            ),
        )
        with patch.object(
            subject.subprocess,
            "Popen",
            side_effect=AssertionError("worker launch occurred before parity preflight"),
        ):
            with self.assertRaises(subject.BranchOutcomeContractError):
                subject.verify_branch_outcomes_from_source(
                    outcomes,
                    receipt,
                    sources=mismatched_sources,
                    evaluator=SyntheticBlindEvaluator(),
                )

    def test_receipt_exact_census_hashes_and_self_hash(self) -> None:
        outcomes = tuple(
            subject.evaluate_branch_source(_source(repeat=i, seed=7 + i), SyntheticBlindEvaluator())
            for i in range(2)
        )
        receipt = subject.build_branch_outcome_receipt(outcomes, implementation_spec=_spec())
        rows = b"".join(row.canonical_json().encode("utf-8") + b"\n" for row in outcomes)
        self.assertEqual(receipt.row_count, 2)
        self.assertEqual(receipt.rows_sha256, _sha(rows))
        self.assertEqual(receipt.outcomes_file_sha256, _sha(rows))
        tampered = receipt.to_dict()
        tampered["row_count"] = 1
        tampered_without_hash = {key: value for key, value in tampered.items() if key != "receipt_sha256"}
        tampered["receipt_sha256"] = _sha(_canonical(tampered_without_hash))
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject.BranchOutcomeReceipt.from_dict(tampered)

    def test_source_replay_rejects_rehashed_receipt_row_and_dependency_tamper(self) -> None:
        sources = (_source(),)
        outcomes = tuple(subject.evaluate_branch_source(source, SyntheticBlindEvaluator()) for source in sources)
        receipt = subject.build_branch_outcome_receipt(outcomes, implementation_spec=_spec())
        subject.verify_branch_outcomes_from_source(
            outcomes, receipt, sources=sources, evaluator=SyntheticBlindEvaluator()
        )
        bad_receipt = receipt.to_dict()
        bad_receipt["evaluator_contract_sha256"] = SHA_C
        partial = {key: value for key, value in bad_receipt.items() if key != "receipt_sha256"}
        bad_receipt["receipt_sha256"] = _sha(_canonical(partial))
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject.verify_branch_outcomes_from_source(
                outcomes,
                subject.BranchOutcomeReceipt.from_dict(bad_receipt),
                sources=sources,
                evaluator=SyntheticBlindEvaluator(),
            )
        dependency = receipt.to_dict()
        dependency["implementation_sha256s"][0][1] = SHA_D
        partial = {key: value for key, value in dependency.items() if key != "receipt_sha256"}
        dependency["receipt_sha256"] = _sha(_canonical(partial))
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject.verify_branch_outcomes_from_source(
                outcomes,
                subject.BranchOutcomeReceipt.from_dict(dependency),
                sources=sources,
                evaluator=SyntheticBlindEvaluator(),
            )

    def test_source_replay_rejects_same_length_output_corruption_and_roster_omission(self) -> None:
        source = _source()
        outcome = subject.evaluate_branch_source(source, SyntheticBlindEvaluator())
        receipt = subject.build_branch_outcome_receipt((outcome,), implementation_spec=_spec())
        corrupt = _source(pre=b"one obligation closeD")
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject.verify_branch_outcomes_from_source(
                (outcome,), receipt, sources=(corrupt,), evaluator=SyntheticBlindEvaluator()
            )
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject.verify_branch_outcomes_from_source(
                (outcome,), receipt, sources=(), evaluator=SyntheticBlindEvaluator()
            )

    def test_source_replay_rejects_foreign_outcome_before_method_access(self) -> None:
        source = _source()
        outcome = subject.evaluate_branch_source(source, SyntheticBlindEvaluator())
        receipt = subject.build_branch_outcome_receipt(
            (outcome,), implementation_spec=_spec()
        )
        observer: list[str] = []

        class ForeignOutcome:
            def canonical_json(self):
                observer.append("canonical_json")
                return outcome.canonical_json()

        with self.assertRaises(TypeError):
            subject.verify_branch_outcomes_from_source(
                (ForeignOutcome(),),  # type: ignore[arg-type]
                receipt,
                sources=(source,),
                evaluator=SyntheticBlindEvaluator(),
            )
        self.assertEqual(observer, [])

    def test_all_public_outcome_table_paths_reject_foreign_rows_without_callbacks(self) -> None:
        observer: list[str] = []

        class ForeignOutcome:
            def canonical_json(self):
                observer.append("canonical_json")
                return "{}"

        foreign = (ForeignOutcome(),)
        calls = (
            lambda: subject.validate_branch_outcome_table(foreign),  # type: ignore[arg-type]
            lambda: subject.build_branch_outcome_receipt(  # type: ignore[arg-type]
                foreign,
                implementation_spec=_spec(),
            ),
        )
        for call in calls:
            with self.subTest(call=call), self.assertRaises(TypeError):
                call()
        self.assertEqual(observer, [])

    def test_raw_json_rejects_duplicates_malformed_utf8_and_noncanonical_bytes(self) -> None:
        outcome = subject.evaluate_branch_source(_source(), SyntheticBlindEvaluator())
        receipt = subject.build_branch_outcome_receipt((outcome,), implementation_spec=_spec())
        rows = outcome.canonical_json().encode() + b"\n"
        subject._parse_outcome_jsonl_bytes_for_test(rows)
        subject._parse_receipt_bytes_for_test(receipt.canonical_json().encode())
        bad_inputs = (
            b'{"schema_version":"x","schema_version":"y"}\n',
            b"\xff",
            rows.replace(b"\n", b"\r\n"),
            rows + b"\n",
            rows[:-1],
        )
        for raw in bad_inputs:
            with self.subTest(raw=raw[:20]), self.assertRaises((UnicodeDecodeError, subject.BranchOutcomeContractError)):
                subject._parse_outcome_jsonl_bytes_for_test(raw)
        pretty = json.dumps(receipt.to_dict(), indent=2).encode()
        with self.assertRaises(subject.BranchOutcomeContractError):
            subject._parse_receipt_bytes_for_test(pretty)

    def test_controller_deserializers_and_serializers_reject_outcomes(self) -> None:
        outcome = subject.evaluate_branch_source(_source(), SyntheticBlindEvaluator())
        with self.assertRaises(ValueError):
            ObligationState.from_dict(outcome.to_dict())
        with self.assertRaises(ValueError):
            ArchitecturePublicCase.from_dict(outcome.to_dict())
        with self.assertRaises(TypeError):
            controller_catalog_bytes(outcome)  # type: ignore[arg-type]
        serialized = outcome.canonical_json()
        self.assertNotIn("evaluator_reference\"", serialized)
        self.assertNotIn("hidden_assessment_target", serialized)

    def test_static_dependency_direction_and_no_semantic_family_action_mapping(self) -> None:
        controller_paths = (
            Path("iclr2027/obligation_contract.py"),
            Path("iclr2027/capability_binding.py"),
            Path("iclr2027/architecture_obligations.py"),
        )
        forbidden = ("obligation_outcomes", "evaluate_iclr2027_obligation_branches", "gold", "mutation", "validator", "evaluator")
        for path in controller_paths:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            imports = " ".join(
                node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
            ) + " " + " ".join(
                alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names
            )
            for token in forbidden:
                self.assertNotIn(token, imports.casefold(), path)
        module_source = Path(subject.__file__).read_text(encoding="utf-8")
        self.assertNotIn("family_to_action", module_source)
        self.assertNotIn("obligation_family", module_source)

    def test_no_reducer_transition_estimator_or_scientific_claim_api(self) -> None:
        banned = ("best", "argmax", "oracle", "stitch", "transition", "e2_pass", "e3_pass", "power", "confidence_interval", "action_regret")
        exported = " ".join(subject.__all__).casefold()
        for token in banned:
            self.assertNotIn(token, exported)
        outcome_fields = {field.name for field in fields(subject.BranchOutcome)}
        self.assertTrue(outcome_fields.isdisjoint({"alignment", "arm", "utility", "policy", "independent_unit", "unsafe_rate"}))
        self.assertIn("E2 primary", subject.__doc__ or "")
        self.assertIn("E3", subject.__doc__ or "")

    def test_private_temp_publication_is_deterministic_and_receipt_last(self) -> None:
        outcome = subject.evaluate_branch_source(_source(), SyntheticBlindEvaluator())
        receipt = subject.build_branch_outcome_receipt((outcome,), implementation_spec=_spec())
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            subject._publish_pair_for_test((outcome,), receipt, Path(first))
            subject._publish_pair_for_test((outcome,), receipt, Path(second))
            for name in ("branch_outcomes.jsonl", "branch_outcomes.receipt.json"):
                self.assertEqual((Path(first) / name).read_bytes(), (Path(second) / name).read_bytes())
            subject._verify_pair_against_expected_for_test((outcome,), receipt, Path(first))
            forged = receipt.to_dict()
            forged["row_count"] = 9
            partial = {key: value for key, value in forged.items() if key != "receipt_sha256"}
            forged["receipt_sha256"] = _sha(_canonical(partial))
            (Path(first) / "branch_outcomes.receipt.json").write_bytes(_canonical(forged))
            with self.assertRaises(subject.BranchOutcomeContractError):
                subject._verify_pair_against_expected_for_test((outcome,), receipt, Path(first))

    def test_private_temp_publication_failure_preserves_prior_pair_or_no_pair(self) -> None:
        outcome = subject.evaluate_branch_source(_source(), SyntheticBlindEvaluator())
        receipt = subject.build_branch_outcome_receipt((outcome,), implementation_spec=_spec())
        with tempfile.TemporaryDirectory() as empty:
            def fail_table_replace(phase):
                if phase == "table-replace":
                    raise OSError("injected table replacement failure")

            with patch.object(
                subject,
                "_publication_phase_hook_for_test",
                side_effect=fail_table_replace,
            ), self.assertRaises(OSError):
                subject._publish_pair_for_test((outcome,), receipt, Path(empty))
            self.assertEqual(tuple(Path(empty).iterdir()), ())
        with tempfile.TemporaryDirectory() as existing:
            root = Path(existing)
            subject._publish_pair_for_test((outcome,), receipt, root)
            before = {path.name: path.read_bytes() for path in root.iterdir()}
            rollback_attempts = 0

            def fail_receipt_then_one_rollback(phase):
                nonlocal rollback_attempts
                if phase == "receipt-replace":
                    raise OSError("injected receipt replacement failure")
                if phase == "rollback-table":
                    rollback_attempts += 1
                    if rollback_attempts == 1:
                        raise OSError("one-shot rollback failure")

            with patch.object(
                subject,
                "_publication_phase_hook_for_test",
                side_effect=fail_receipt_then_one_rollback,
            ), self.assertRaises(OSError):
                subject._publish_pair_for_test((outcome,), receipt, root)
            after = {path.name: path.read_bytes() for path in root.iterdir()}
            self.assertEqual(after, before)
            self.assertEqual(rollback_attempts, 2)

    def test_publication_rejects_hardlink_temp_substitution_before_replace(self) -> None:
        outcome = subject.evaluate_branch_source(_source(), SyntheticBlindEvaluator())
        receipt = subject.build_branch_outcome_receipt((outcome,), implementation_spec=_spec())
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as attack_directory:
            root = Path(directory)
            outside = Path(attack_directory) / "attacker-owned-bytes"
            outside.write_bytes(b"x" * len(outcome.canonical_json().encode("utf-8") + b"\n"))
            substituted = False
            attack_denied = False

            def substitute_temp(phase):
                nonlocal substituted, attack_denied
                if phase != "table-replace":
                    return
                candidates = tuple(
                    path
                    for path in root.iterdir()
                    if path.name
                    not in {
                        ".branch_outcomes.lock",
                        ".branch_outcomes.quarantine",
                        "branch_outcomes.jsonl",
                        "branch_outcomes.receipt.json",
                    }
                )
                self.assertEqual(len(candidates), 2)
                table_temp = next(
                    path
                    for path in candidates
                    if path.stat().st_size
                    == len(outcome.canonical_json().encode("utf-8") + b"\n")
                )
                try:
                    table_temp.unlink()
                    os.link(outside, table_temp)
                    substituted = True
                except OSError:
                    attack_denied = True

            observed: BaseException | None = None
            with patch.object(
                subject,
                "_publication_phase_hook_for_test",
                side_effect=substitute_temp,
            ):
                try:
                    subject._publish_pair_for_test((outcome,), receipt, root)
                except BaseException as error:
                    observed = error
            self.assertTrue(substituted or attack_denied)
            if substituted:
                self.assertIsInstance(observed, subject.BranchOutcomeContractError)
                self.assertFalse((root / "branch_outcomes.jsonl").exists())
                self.assertFalse((root / "branch_outcomes.receipt.json").exists())
            else:
                self.assertIsNone(observed)
                subject._verify_pair_against_expected_for_test(
                    (outcome,), receipt, root
                )

    def test_temp_substitution_preserves_an_existing_verified_pair(self) -> None:
        old_outcome = subject.evaluate_branch_source(_source(), SyntheticBlindEvaluator())
        old_receipt = subject.build_branch_outcome_receipt(
            (old_outcome,), implementation_spec=_spec()
        )
        new_outcome = subject.evaluate_branch_source(
            _source(repeat=1, seed=8), SyntheticBlindEvaluator()
        )
        new_receipt = subject.build_branch_outcome_receipt(
            (new_outcome,), implementation_spec=_spec()
        )
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as attack_directory:
            root = Path(directory)
            subject._publish_pair_for_test((old_outcome,), old_receipt, root)
            before = {
                name: (root / name).read_bytes()
                for name in (
                    "branch_outcomes.jsonl",
                    "branch_outcomes.receipt.json",
                )
            }
            attacker = Path(attack_directory) / "attacker-owned-bytes"
            attacker.write_bytes(
                b"x" * len(new_outcome.canonical_json().encode("utf-8") + b"\n")
            )
            substituted = False
            attack_denied = False

            def substitute_temp(phase):
                nonlocal substituted, attack_denied
                if phase != "table-replace":
                    return
                candidates = tuple(
                    path
                    for path in root.iterdir()
                    if path.name
                    not in {
                        ".branch_outcomes.lock",
                        ".branch_outcomes.quarantine",
                        "branch_outcomes.jsonl",
                        "branch_outcomes.receipt.json",
                    }
                )
                table_temp = next(
                    path
                    for path in candidates
                    if path.stat().st_size
                    == len(new_outcome.canonical_json().encode("utf-8") + b"\n")
                )
                try:
                    table_temp.unlink()
                    os.link(attacker, table_temp)
                    substituted = True
                except OSError:
                    attack_denied = True

            observed: BaseException | None = None
            with patch.object(
                subject,
                "_publication_phase_hook_for_test",
                side_effect=substitute_temp,
            ):
                try:
                    subject._publish_pair_for_test(
                        (new_outcome,), new_receipt, root
                    )
                except BaseException as error:
                    observed = error
            self.assertTrue(substituted or attack_denied)
            if substituted:
                self.assertIsInstance(observed, subject.BranchOutcomeContractError)
            else:
                self.assertIsNone(observed)
            after = {name: (root / name).read_bytes() for name in before}
            self.assertEqual(after, before if substituted else {
                "branch_outcomes.jsonl": new_outcome.canonical_json().encode("utf-8") + b"\n",
                "branch_outcomes.receipt.json": new_receipt.canonical_json().encode("utf-8"),
            })

    def test_publication_rejects_stale_mismatched_prior_pair_without_overwrite(self) -> None:
        outcome = subject.evaluate_branch_source(_source(), SyntheticBlindEvaluator())
        receipt = subject.build_branch_outcome_receipt((outcome,), implementation_spec=_spec())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            table = root / "branch_outcomes.jsonl"
            receipt_path = root / "branch_outcomes.receipt.json"
            table.write_bytes(b"stale-table\n")
            receipt_path.write_bytes(b'{"stale":true}')
            before = (table.read_bytes(), receipt_path.read_bytes())
            with self.assertRaises(subject.BranchOutcomeContractError):
                subject._publish_pair_for_test((outcome,), receipt, root)
            self.assertEqual((table.read_bytes(), receipt_path.read_bytes()), before)

    def test_receipt_commit_then_restore_failure_never_leaves_mixed_pair_or_residue(self) -> None:
        old_outcome = subject.evaluate_branch_source(_source(), SyntheticBlindEvaluator())
        old_receipt = subject.build_branch_outcome_receipt((old_outcome,), implementation_spec=_spec())
        new_outcome = subject.evaluate_branch_source(
            _source(repeat=1, seed=8), SyntheticBlindEvaluator()
        )
        new_receipt = subject.build_branch_outcome_receipt((new_outcome,), implementation_spec=_spec())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subject._publish_pair_for_test((old_outcome,), old_receipt, root)
            def fail_receipt_commit_and_persistently_fail_restore(phase):
                if phase == "receipt-replace":
                    raise OSError("injected receipt commit failure")
                if phase == "rollback-receipt":
                    raise OSError("injected persistent receipt restore failure")

            with patch.object(
                subject,
                "_publication_phase_hook_for_test",
                side_effect=fail_receipt_commit_and_persistently_fail_restore,
            ):
                with self.assertRaises(OSError):
                    subject._publish_pair_for_test(
                        (new_outcome,), new_receipt, root
                    )
            quarantine = root / ".branch_outcomes.quarantine"
            self.assertTrue(quarantine.is_file())
            marker = json.loads(quarantine.read_bytes())
            unsigned = {
                key: value for key, value in marker.items()
                if key != "quarantine_sha256"
            }
            self.assertEqual(
                marker,
                {
                    "schema_version": "ace.iclr2027.branch_outcome_quarantine.v1",
                    "state": "recovery_required",
                    "reason_code": "restore_failed",
                    "quarantine_sha256": _sha(_canonical(unsigned)),
                },
            )
            with self.assertRaises(subject.BranchOutcomeContractError):
                subject._verify_pair_against_expected_for_test(
                    (old_outcome,), old_receipt, root
                )

    def test_post_table_replace_validation_failure_restores_prior_pair(self) -> None:
        old_outcome = subject.evaluate_branch_source(
            _source(), SyntheticBlindEvaluator()
        )
        old_receipt = subject.build_branch_outcome_receipt(
            (old_outcome,), implementation_spec=_spec()
        )
        new_outcome = subject.evaluate_branch_source(
            _source(repeat=1, seed=8), SyntheticBlindEvaluator()
        )
        new_receipt = subject.build_branch_outcome_receipt(
            (new_outcome,), implementation_spec=_spec()
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subject._publish_pair_for_test((old_outcome,), old_receipt, root)
            prior = {
                name: (root / name).read_bytes()
                for name in (
                    "branch_outcomes.jsonl",
                    "branch_outcomes.receipt.json",
                )
            }
            original_replace = subject._PublicationCapability.replace

            def replace_then_fail(capability, leaf, final_name, *, phase):
                original_replace(
                    capability, leaf, final_name, phase=phase
                )
                if phase == "table-replace":
                    raise subject.BranchOutcomeContractError(
                        "injected post-table-rename identity failure"
                    )

            with patch.object(
                subject._PublicationCapability,
                "replace",
                new=replace_then_fail,
            ), self.assertRaises(subject.BranchOutcomeContractError):
                subject._publish_pair_for_test((new_outcome,), new_receipt, root)
            self.assertEqual(
                {name: (root / name).read_bytes() for name in prior}, prior
            )

    def test_primary_failure_with_persistent_unlock_cleanup_quarantines(self) -> None:
        outcome = subject.evaluate_branch_source(_source(), SyntheticBlindEvaluator())
        receipt = subject.build_branch_outcome_receipt(
            (outcome,), implementation_spec=_spec()
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original_cleanup = subject._PublicationCapability.cleanup_leaf

            def persistent_lock_cleanup_failure(capability, leaf):
                if leaf.name == ".branch_outcomes.lock":
                    raise OSError("injected persistent unlock failure")
                return original_cleanup(capability, leaf)

            def fail_table_replace(phase):
                if phase == "table-replace":
                    raise OSError("injected primary publication failure")

            with patch.object(
                subject._PublicationCapability,
                "cleanup_leaf",
                new=persistent_lock_cleanup_failure,
            ), patch.object(
                subject,
                "_publication_phase_hook_for_test",
                side_effect=fail_table_replace,
            ), self.assertRaises(OSError):
                subject._publish_pair_for_test((outcome,), receipt, root)
            marker = root / ".branch_outcomes.quarantine"
            self.assertTrue(marker.is_file())
            payload = json.loads(marker.read_bytes())
            self.assertEqual(payload["reason_code"], "cleanup_failed")
            with self.assertRaises(subject.BranchOutcomeContractError):
                subject._verify_pair_against_expected_for_test(
                    (outcome,), receipt, root
                )

    def test_fsync_failure_before_replace_leaves_no_pair_or_temp_residue(self) -> None:
        outcome = subject.evaluate_branch_source(_source(), SyntheticBlindEvaluator())
        receipt = subject.build_branch_outcome_receipt((outcome,), implementation_spec=_spec())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def fail_receipt_temp_fsync(phase):
                if phase == "receipt-temp-fsync":
                    raise OSError("injected receipt temporary fsync failure")

            with patch.object(
                subject,
                "_publication_phase_hook_for_test",
                side_effect=fail_receipt_temp_fsync,
            ), self.assertRaises(OSError):
                subject._publish_pair_for_test((outcome,), receipt, root)
            self.assertEqual(tuple(root.iterdir()), ())

    def test_cli_source_mode_is_no_io_needs_context_and_surface_has_no_callbacks(self) -> None:
        cli = importlib.import_module("evaluate_iclr2027_obligation_branches")
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "must-not-be-touched"
            with self.assertRaisesRegex(SystemExit, "NEEDS_CONTEXT"):
                cli.main(["--mode", "source", "--source-receipt", str(marker), "--output-dir", str(marker)])
            self.assertFalse(marker.exists())
        parser = cli._build_parser()
        actions = {option for action in parser._actions for option in action.option_strings}
        self.assertEqual(actions, {"-h", "--help", "--mode", "--source-receipt", "--output-dir"})
        self.assertTrue(actions.isdisjoint({"--callback", "--controller", "--policy", "--in-process", "--spec"}))

    def test_source_adapter_and_production_spec_factory_are_deliberately_unavailable(self) -> None:
        self.assertFalse(hasattr(subject, "load_branch_sources"))
        self.assertFalse(hasattr(subject, "from_source_receipt"))
        self.assertFalse(hasattr(subject.EvaluationImplementationSpec, "from_source"))
        self.assertFalse(hasattr(subject, "publish_branch_outcomes"))
        self.assertFalse(hasattr(subject, "verify_branch_outcomes_output_only"))

    def test_phase4a_has_no_focal_roster_or_production_authentication_path(self) -> None:
        self.assertTrue(_spec().test_only)
        for name in (
            "AuthenticatedTask4ImplementationTrustRoot",
            "FrozenBranchAssignment",
            "load_focal_branch_roster",
            "authenticate_production_implementation_spec",
            "publish_source_branch_outcomes",
        ):
            with self.subTest(name=name):
                self.assertFalse(hasattr(subject, name))
                self.assertNotIn(name, subject.__all__)


if __name__ == "__main__":
    unittest.main()
