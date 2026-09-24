from __future__ import annotations

import ast
import hashlib
import inspect
import json
import math
from pathlib import Path
import unittest

from iclr2027.architecture_obligations import (
    declared_architecture_obligations,
    public_obligation_state,
    validate_public_architecture_admission,
)
from iclr2027.obligation_contract import ObligationSpec, ObligationState
from iclr2027.review_state import PrefixReviewState
from iclr2027.schema import ArchitecturePublicCase, ArchitectureReviewState


_CASE_ID = "case:" + "a" * 64
_SITE_REF = "site:" + "b" * 64
_PROGRAM_HASH = "c" * 64
_GEOMETRY_HASH = "d" * 64
_SOURCE_HASH = "e" * 64
_REQUIRED_EVIDENCE = (
    "evidence:site_agent",
    "evidence:law_graph_agent",
    "evidence:parking_agent",
    "evidence:program_agent",
    "evidence:geometry_agent",
)
_EXPECTED_SPECS = (
    {
        "obligation_id": "obligation:architecture:site/evidence",
        "family": "site/evidence",
        "weight": 1.0,
        "hard": True,
        "public_basis_ids": [
            "task:architecture_review",
            "evidence:site_agent",
        ],
    },
    {
        "obligation_id": "obligation:architecture:law",
        "family": "law",
        "weight": 1.0,
        "hard": True,
        "public_basis_ids": [
            "task:architecture_review",
            "evidence:law_graph_agent",
        ],
    },
    {
        "obligation_id": "obligation:architecture:parking",
        "family": "parking",
        "weight": 1.0,
        "hard": True,
        "public_basis_ids": [
            "task:architecture_review",
            "evidence:parking_agent",
        ],
    },
    {
        "obligation_id": "obligation:architecture:program",
        "family": "program",
        "weight": 1.0,
        "hard": True,
        "public_basis_ids": [
            "task:architecture_review",
            "evidence:program_agent",
        ],
    },
    {
        "obligation_id": "obligation:architecture:geometry",
        "family": "geometry",
        "weight": 1.0,
        "hard": True,
        "public_basis_ids": [
            "task:architecture_review",
            "evidence:geometry_agent",
        ],
    },
)


def _site_record(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "evidence_id": "evidence:site_agent",
        "domain": "site",
        "status": "passed",
        "evidence": {
            "site_ref": _SITE_REF,
            "inside_site": True,
            "geometry_hash": _GEOMETRY_HASH,
        },
    }
    record.update(overrides)
    return record


def _domain_record(
    evidence_id: str, domain: str, status: str = "passed"
) -> dict[str, object]:
    return {
        "evidence_id": evidence_id,
        "domain": domain,
        "status": status,
        "evidence": {"public_summary": f"{domain}-summary"},
    }


def _full_evidence(*, law_status: str = "passed") -> tuple[dict[str, object], ...]:
    return (
        _site_record(),
        _domain_record("evidence:law_graph_agent", "law", law_status),
        _domain_record("evidence:parking_agent", "parking"),
        _domain_record("evidence:program_agent", "program"),
        _domain_record("evidence:geometry_agent", "geometry"),
    )


def _case(
    evidence: tuple[dict[str, object], ...] | None = None,
    *,
    source_hash: str | None = _SOURCE_HASH,
) -> ArchitecturePublicCase:
    return ArchitecturePublicCase(
        case_id=_CASE_ID,
        site_ref=_SITE_REF,
        program="neighborhood",
        execution_id="execution:public-fixture",
        program_hash=_PROGRAM_HASH,
        geometry_hash=_GEOMETRY_HASH,
        evidence=evidence if evidence is not None else _full_evidence(),
        subject_kind="execution",
        source_artifact_sha256=source_hash,
    )


def _portfolio_case() -> ArchitecturePublicCase:
    return ArchitecturePublicCase(
        case_id=_CASE_ID,
        site_ref=_SITE_REF,
        program="neighborhood",
        execution_id=None,
        program_hash=None,
        geometry_hash=None,
        evidence=(_domain_record("evidence:portfolio_attempt", "program", "failed"),),
        subject_kind="portfolio_attempt",
        source_artifact_sha256=_SOURCE_HASH,
        attempt_id="attempt:" + "f" * 64,
        attempt_hash="1" * 64,
        attempt_stage="selection",
    )


def _prefix(
    *,
    checked: tuple[str, ...] = (),
    issues: tuple[str, ...] = (),
    missing: tuple[str, ...] = (),
    cited: tuple[str, ...] = (),
    decision: str = "CONTINUE",
    complete: bool = True,
    errors: tuple[str, ...] = (),
    turn_index: int = 0,
) -> PrefixReviewState:
    return PrefixReviewState(
        turn_index=turn_index,
        state=ArchitectureReviewState(
            checked_domains=checked,
            blocking_issue_codes=issues,
            missing_evidence_codes=missing,
            evidence_ids=cited,
            recommended_decision=decision,  # type: ignore[arg-type]
            confidence=0.75,
        ),
        parse_complete=complete,
        parse_error_codes=errors,
    )


def _beliefs_by_family(state: ObligationState) -> dict[str, dict[str, object]]:
    family_by_id = {item["obligation_id"]: item["family"] for item in _EXPECTED_SPECS}
    return {
        family_by_id[belief.obligation_id]: belief.to_dict() for belief in state.beliefs
    }


class ArchitectureObligationDeclarationTests(unittest.TestCase):
    def test_exact_stable_five_family_declaration_is_status_independent(self) -> None:
        passed = declared_architecture_obligations(_case())
        changed_status = declared_architecture_obligations(
            _case(_full_evidence(law_status="not_reviewed"))
        )

        self.assertEqual(tuple(spec.to_dict() for spec in passed), _EXPECTED_SPECS)
        self.assertEqual(passed, changed_status)
        self.assertTrue(all(type(spec) is ObligationSpec for spec in passed))
        self.assertEqual(
            tuple(inspect.signature(declared_architecture_obligations).parameters),
            ("public_case",),
        )

    def test_declaration_keeps_all_families_when_law_and_parking_are_absent(
        self,
    ) -> None:
        evidence = tuple(
            record
            for record in _full_evidence()
            if record["evidence_id"]
            not in {"evidence:law_graph_agent", "evidence:parking_agent"}
        )

        specs = declared_architecture_obligations(_case(evidence))

        self.assertEqual(
            tuple(spec.family for spec in specs),
            (
                "site/evidence",
                "law",
                "parking",
                "program",
                "geometry",
            ),
        )

    def test_exact_type_and_execution_subject_are_required(self) -> None:
        with self.assertRaisesRegex(TypeError, "ArchitecturePublicCase"):
            declared_architecture_obligations(_case().to_dict())  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "execution"):
            declared_architecture_obligations(_portfolio_case())


class ArchitectureAdmissionTests(unittest.TestCase):
    def test_exact_site_grammar_and_authenticated_source_are_admitted(self) -> None:
        self.assertIsNone(validate_public_architecture_admission(_case()))

        with self.assertRaisesRegex(TypeError, "ArchitecturePublicCase"):
            validate_public_architecture_admission(_case().to_dict())  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "execution"):
            validate_public_architecture_admission(_portfolio_case())

    def test_missing_or_tampered_source_hash_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "source_artifact_sha256"):
            validate_public_architecture_admission(_case(source_hash=None))

        tampered = _case()
        object.__setattr__(tampered, "source_artifact_sha256", "not-a-sha")
        with self.assertRaisesRegex(ValueError, "source_artifact_sha256"):
            validate_public_architecture_admission(tampered)

    def test_site_outer_keys_and_fixed_values_are_exact(self) -> None:
        malformed_records: tuple[dict[str, object], ...] = (
            _site_record(status="failed"),
            _site_record(domain="geometry"),
            _site_record(evidence_id="evidence:wrong_site"),
            _site_record(extra="not-allowed"),
            {
                "evidence_id": "evidence:site_agent",
                "domain": "site",
                "evidence": _site_record()["evidence"],
            },
        )
        tail = _full_evidence()[1:]
        for record in malformed_records:
            with self.subTest(record=record):
                with self.assertRaises((TypeError, ValueError)):
                    validate_public_architecture_admission(_case((record, *tail)))

    def test_site_nested_keys_and_native_inside_boolean_are_exact(self) -> None:
        malformed_records: tuple[dict[str, object], ...] = (
            _site_record(evidence={"site_ref": _SITE_REF, "inside_site": True}),
            _site_record(
                evidence={
                    "site_ref": _SITE_REF,
                    "inside_site": True,
                    "geometry_hash": _GEOMETRY_HASH,
                    "extra": "not-allowed",
                }
            ),
            _site_record(
                evidence={
                    "site_ref": _SITE_REF,
                    "inside_site": False,
                    "geometry_hash": _GEOMETRY_HASH,
                }
            ),
            _site_record(
                evidence={
                    "site_ref": _SITE_REF,
                    "inside_site": 1,
                    "geometry_hash": _GEOMETRY_HASH,
                }
            ),
            _site_record(evidence="not-a-mapping"),
        )
        tail = _full_evidence()[1:]
        for record in malformed_records:
            with self.subTest(record=record):
                with self.assertRaises((TypeError, ValueError)):
                    validate_public_architecture_admission(_case((record, *tail)))

    def test_site_reference_and_geometry_identity_must_match_the_case(self) -> None:
        mismatched_records = (
            _site_record(
                evidence={
                    "site_ref": "site:" + "9" * 64,
                    "inside_site": True,
                    "geometry_hash": _GEOMETRY_HASH,
                }
            ),
            _site_record(
                evidence={
                    "site_ref": _SITE_REF,
                    "inside_site": True,
                    "geometry_hash": "8" * 64,
                }
            ),
        )
        tail = _full_evidence()[1:]
        for record in mismatched_records:
            with self.subTest(record=record):
                with self.assertRaises((TypeError, ValueError)):
                    validate_public_architecture_admission(_case((record, *tail)))

    def test_site_record_is_required_and_no_second_site_domain_is_allowed(self) -> None:
        no_site = tuple(
            record for record in _full_evidence() if record["domain"] != "site"
        )
        with self.assertRaisesRegex(ValueError, "site"):
            validate_public_architecture_admission(_case(no_site))

        duplicate_site_domain = (
            *_full_evidence(),
            _domain_record("evidence:other", "site"),
        )
        with self.assertRaisesRegex(ValueError, "site"):
            validate_public_architecture_admission(_case(duplicate_site_domain))

    def test_admission_failure_precedes_prefix_observation(self) -> None:
        class ExplodingPrefix:
            def __getattribute__(self, name: str) -> object:
                raise AssertionError(f"prefix was observed through {name}")

        with self.assertRaisesRegex(ValueError, "source_artifact_sha256"):
            public_obligation_state(
                _case(source_hash=None),
                ExplodingPrefix(),  # type: ignore[arg-type]
            )


class ArchitecturePublicStateTests(unittest.TestCase):
    def test_prefix_id_uses_the_exact_frozen_canonical_payload(self) -> None:
        case = _case()
        prefix = _prefix(
            checked=("site", "law"),
            cited=("evidence:site_agent", "evidence:law_graph_agent"),
            errors=("diagnostic-order-one", "diagnostic-order-two"),
            turn_index=3,
        )
        payload = {
            "schema_version": "iclr2027.architecture_obligation_prefix.v1",
            "public_case": case.to_dict(),
            "prefix": {
                "turn_index": prefix.turn_index,
                "state": prefix.state.to_dict(),
                "parse_complete": prefix.parse_complete,
                "parse_error_codes": list(prefix.parse_error_codes),
            },
        }
        expected = (
            "prefix:"
            + hashlib.sha256(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    allow_nan=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
        )

        state = public_obligation_state(case, prefix)

        self.assertEqual(state.prefix_id, expected)
        self.assertEqual(state.case_id, case.case_id)

    def test_absent_evidence_and_agent_reported_missing_are_distinct(self) -> None:
        evidence = tuple(
            record
            for record in _full_evidence()
            if record["evidence_id"]
            not in {"evidence:law_graph_agent", "evidence:parking_agent"}
        )
        case = _case(evidence)
        silent = public_obligation_state(
            case,
            _prefix(checked=("law", "parking")),
        )
        reported = public_obligation_state(
            case,
            _prefix(
                checked=("law", "parking"),
                missing=(
                    "law.required_evidence_missing",
                    "parking.required_evidence_missing",
                ),
            ),
        )

        silent_beliefs = _beliefs_by_family(silent)
        reported_beliefs = _beliefs_by_family(reported)
        for family in ("law", "parking"):
            self.assertEqual(silent_beliefs[family]["status"], "unknown")
            self.assertEqual(silent_beliefs[family]["unresolved_probability"], 0.5)
            self.assertEqual(reported_beliefs[family]["status"], "unresolved")
            self.assertEqual(reported_beliefs[family]["unresolved_probability"], 1.0)
        self.assertFalse(silent.hard_gate_passed)
        self.assertFalse(reported.hard_gate_passed)

    def test_prefix_authored_beliefs_transition_without_status_or_truth_inference(
        self,
    ) -> None:
        case = _case(_full_evidence(law_status="failed"))
        unchecked = _beliefs_by_family(public_obligation_state(case, _prefix()))
        resolved = _beliefs_by_family(
            public_obligation_state(
                case,
                _prefix(
                    checked=("law",),
                    cited=("evidence:law_graph_agent",),
                ),
            )
        )
        unresolved = _beliefs_by_family(
            public_obligation_state(
                case,
                _prefix(
                    checked=("site", "law"),
                    issues=("identity.hash_mismatch", "law.projection_failed"),
                    cited=("evidence:site_agent", "evidence:law_graph_agent"),
                ),
            )
        )

        self.assertEqual(
            (unchecked["law"]["status"], unchecked["law"]["unresolved_probability"]),
            ("unknown", 0.5),
        )
        self.assertEqual(
            (resolved["law"]["status"], resolved["law"]["unresolved_probability"]),
            ("resolved", 0.0),
        )
        self.assertEqual(
            (unresolved["law"]["status"], unresolved["law"]["unresolved_probability"]),
            ("unresolved", 1.0),
        )
        self.assertEqual(unresolved["site/evidence"]["status"], "unresolved")

    def test_all_allowed_code_prefixes_map_and_unknown_prefixes_fail_closed(
        self,
    ) -> None:
        expected = {
            "site.boundary_failed": "site/evidence",
            "identity.hash_mismatch": "site/evidence",
            "evidence.portfolio_attempt_incomplete": "site/evidence",
            "law.projection_failed": "law",
            "parking.supply_shortage": "parking",
            "program.capacity_failed": "program",
            "geometry.compilation_failed": "geometry",
        }
        for code, family in expected.items():
            with self.subTest(code=code):
                beliefs = _beliefs_by_family(
                    public_obligation_state(_case(), _prefix(issues=(code,)))
                )
                self.assertEqual(beliefs[family]["status"], "unresolved")

        for code in (
            "zoning.observed_problem",
            "candidate_floor_context.typed_ledger_missing",
            "law",
        ):
            with self.subTest(code=code):
                prefix = _prefix(
                    missing=(code,)
                    if code == "candidate_floor_context.typed_ledger_missing"
                    else ()
                )
                if code != "candidate_floor_context.typed_ledger_missing":
                    object.__setattr__(prefix.state, "blocking_issue_codes", (code,))
                with self.assertRaisesRegex(ValueError, "unknown.*prefix"):
                    public_obligation_state(_case(), prefix)

    def test_hard_gate_is_exactly_the_public_process_gate(self) -> None:
        checked = ("site", "law", "parking", "program", "geometry")
        base = {
            "checked": checked,
            "cited": _REQUIRED_EVIDENCE,
            "decision": "STOP_ACCEPT",
            "complete": True,
        }
        self.assertTrue(
            public_obligation_state(_case(), _prefix(**base)).hard_gate_passed
        )

        false_prefixes = (
            _prefix(**{**base, "cited": _REQUIRED_EVIDENCE[:-1]}),
            _prefix(**{**base, "complete": False, "errors": ("malformed_json",)}),
            _prefix(**{**base, "decision": "CONTINUE"}),
            _prefix(**{**base, "checked": checked[:-1]}),
            _prefix(**{**base, "missing": ("law.required_evidence_missing",)}),
        )
        for prefix in false_prefixes:
            with self.subTest(prefix=prefix):
                self.assertFalse(
                    public_obligation_state(_case(), prefix).hard_gate_passed
                )

        absent_law = tuple(
            record
            for record in _full_evidence()
            if record["evidence_id"] != "evidence:law_graph_agent"
        )
        self.assertFalse(
            public_obligation_state(
                _case(absent_law),
                _prefix(**base),
            ).hard_gate_passed
        )

        extra_public_record = (
            *_full_evidence(),
            _domain_record("evidence:review_agent", "program"),
        )
        self.assertFalse(
            public_obligation_state(
                _case(extra_public_record),
                _prefix(**base),
            ).hard_gate_passed
        )
        self.assertTrue(
            public_obligation_state(
                _case(extra_public_record),
                _prefix(
                    **{
                        **base,
                        "cited": (*_REQUIRED_EVIDENCE, "evidence:review_agent"),
                    }
                ),
            ).hard_gate_passed
        )

    def test_parse_error_tuple_keeps_an_otherwise_complete_direct_prefix_gated(
        self,
    ) -> None:
        prefix = PrefixReviewState(
            turn_index=4,
            state=ArchitectureReviewState(
                checked_domains=("site", "law", "parking", "program", "geometry"),
                blocking_issue_codes=(),
                missing_evidence_codes=(),
                evidence_ids=_REQUIRED_EVIDENCE,
                recommended_decision="STOP_ACCEPT",
                confidence=0.9,
            ),
            parse_complete=True,
            parse_error_codes=("malformed_json",),
        )

        state = public_obligation_state(_case(), prefix)

        self.assertFalse(state.hard_gate_passed)

    def test_unknown_citation_keeps_an_otherwise_complete_direct_prefix_gated(
        self,
    ) -> None:
        prefix = PrefixReviewState(
            turn_index=4,
            state=ArchitectureReviewState(
                checked_domains=("site", "law", "parking", "program", "geometry"),
                blocking_issue_codes=(),
                missing_evidence_codes=(),
                evidence_ids=(*_REQUIRED_EVIDENCE, "evidence:unknown_agent"),
                recommended_decision="STOP_ACCEPT",
                confidence=0.9,
            ),
            parse_complete=True,
            parse_error_codes=(),
        )

        state = public_obligation_state(_case(), prefix)

        self.assertFalse(state.hard_gate_passed)

    def test_cumulative_cost_uses_task_one_validation_and_state_has_no_action_fields(
        self,
    ) -> None:
        state = public_obligation_state(_case(), _prefix(), cumulative_cost=-0.0)
        self.assertEqual(state.cumulative_cost, 0.0)
        self.assertEqual(math.copysign(1.0, state.cumulative_cost), 1.0)
        self.assertEqual(
            set(state.to_dict()),
            {"case_id", "prefix_id", "beliefs", "hard_gate_passed", "cumulative_cost"},
        )
        self.assertTrue(
            all(
                set(belief)
                == {
                    "obligation_id",
                    "status",
                    "unresolved_probability",
                    "evidence_ids",
                }
                for belief in state.to_dict()["beliefs"]
            )
        )
        forbidden = {
            "action",
            "packet",
            "slot",
            "role",
            "topology",
            "mutation",
            "gold",
            "expected_decision",
            "evaluator",
            "hidden_issue",
        }
        serialized = state.canonical_json().casefold()
        for token in forbidden:
            self.assertNotIn(token, serialized)

        for bad_cost in (-1.0, float("nan"), float("inf"), True):
            with self.subTest(cost=bad_cost):
                with self.assertRaises((TypeError, ValueError)):
                    public_obligation_state(
                        _case(), _prefix(), cumulative_cost=bad_cost
                    )

    def test_malformed_prefix_types_fail_closed(self) -> None:
        malformed_prefixes = (
            PrefixReviewState(True, _prefix().state, True, ()),
            PrefixReviewState(0, _prefix().state, 1, ()),
            PrefixReviewState(0, _prefix().state, True, []),
            PrefixReviewState(0, _prefix().state, True, (1,)),
            PrefixReviewState(
                0,
                ArchitectureReviewState(
                    checked_domains=["law"],  # type: ignore[arg-type]
                    blocking_issue_codes=(),
                    missing_evidence_codes=(),
                    evidence_ids=(),
                    recommended_decision="CONTINUE",
                    confidence=0.5,
                ),
                True,
                (),
            ),
        )
        for prefix in malformed_prefixes:
            with self.subTest(prefix=prefix):
                with self.assertRaises(TypeError):
                    public_obligation_state(_case(), prefix)

        with self.assertRaisesRegex(TypeError, "PrefixReviewState"):
            public_obligation_state(_case(), object())  # type: ignore[arg-type]

    def test_hidden_fixture_is_not_an_input_and_cannot_change_any_public_output(
        self,
    ) -> None:
        case = _case()
        prefix = _prefix(
            checked=("site", "law"),
            issues=("law.projection_failed",),
            cited=("evidence:site_agent", "evidence:law_graph_agent"),
        )
        hidden_fixture = {
            "mutation_family": "first-hidden-value",
            "gold": {"expected_decision": "STOP_ACCEPT"},
        }
        before_specs = declared_architecture_obligations(case)
        before_state = public_obligation_state(case, prefix)
        hidden_fixture["mutation_family"] = "second-hidden-value"
        hidden_fixture["gold"] = {"expected_decision": "STOP_REJECT"}
        after_specs = declared_architecture_obligations(case)
        after_state = public_obligation_state(case, prefix)

        self.assertEqual(before_specs, after_specs)
        self.assertEqual(before_state, after_state)
        self.assertEqual(before_state.canonical_json(), after_state.canonical_json())
        self.assertEqual(before_state.sha256(), after_state.sha256())
        with self.assertRaises(TypeError):
            public_obligation_state(case, prefix, gold=hidden_fixture)  # type: ignore[call-arg]


class ArchitectureObligationStaticBoundaryTests(unittest.TestCase):
    def test_ast_has_no_forbidden_import_or_semantic_action_mapping(self) -> None:
        source_path = (
            Path(__file__).resolve().parents[1]
            / "iclr2027"
            / "architecture_obligations.py"
        )
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules: set[str] = set()
        names: set[str] = set()
        string_constants: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name.casefold() for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_modules.add((node.module or "").casefold())
            elif isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                string_constants.add(node.value)

        forbidden_import_parts = ("validators", "metrics", "fault", "gold", "outcome")
        self.assertFalse(
            any(
                part in module
                for module in imported_modules
                for part in forbidden_import_parts
            ),
            imported_modules,
        )
        self.assertNotIn("CoordinationAction", names)
        forbidden_actions = {
            "STOP",
            "SOLO_SYNTHESIS",
            "ASK_LAW",
            "ASK_PARKING",
            "ASK_PROGRAM",
            "ASK_GEOMETRY",
        }
        self.assertTrue(forbidden_actions.isdisjoint(string_constants))


if __name__ == "__main__":
    unittest.main()
