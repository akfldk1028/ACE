from __future__ import annotations

import json
import re
import unittest
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from iclr2027.exp08 import render_case_prompt
from iclr2027.io import sha256_json
from iclr2027.projection import ProjectionIdentity, project_public_case
from iclr2027.schema import ArchitectureEvidencePacket, ArchitecturePublicCase


_RAW_PNU = re.compile(r"(?<!\d)\d{19}(?!\d)")
_IDENTITY = ProjectionIdentity(bytes(range(32)))


def _packet(*, case_id: str, pnu: str) -> ArchitectureEvidencePacket:
    return ArchitectureEvidencePacket(
        case_id=case_id,
        pnu=pnu,
        program="neighborhood",
        condition="challenged",
        execution_id="execution-1",
        program_hash="a" * 64,
        geometry_hash="b" * 64,
        evidence=(
            {
                "evidence_id": "evidence:site",
                "parcel": {
                    "pnu": pnu,
                    "adjacent_identifiers": ["1111010100100000001"],
                    "case_id": case_id,
                    "condition": "challenged",
                },
            },
        ),
    )


def _public(packet: ArchitectureEvidencePacket) -> ArchitecturePublicCase:
    return project_public_case(packet, _IDENTITY)


def _prompt_payload(packet: ArchitectureEvidencePacket) -> dict[str, Any]:
    prompt = render_case_prompt(_public(packet))
    serialized = prompt.split("EVIDENCE_PACKET\n", 1)[1].split(
        "\nEND_EVIDENCE_PACKET", 1
    )[0]
    payload = json.loads(serialized)
    if not isinstance(payload, dict):
        raise AssertionError("rendered prompt payload must be a JSON object")
    return payload


def _walk(value: Any):
    yield value
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield from _walk(key)
            yield from _walk(item)
    elif isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for item in value:
            yield from _walk(item)


class Exp08PublicPromptTests(unittest.TestCase):
    def test_shipped_state_example_is_parse_valid_under_its_own_rules(self) -> None:
        from iclr2027.prompts import ARCH_REVIEW_STATE_BLOCK
        from iclr2027.review_state import parse_review_state

        parsed = parse_review_state(ARCH_REVIEW_STATE_BLOCK)

        self.assertTrue(parsed.complete)
        self.assertEqual(parsed.error_codes, ())
        self.assertEqual(
            parsed.state.missing_evidence_codes,
            ("parking.required_evidence_missing",),
        )

    def test_accept_template_covers_every_admissibility_domain(self) -> None:
        from iclr2027.architecture_metrics import score_prefix, score_prefix_breakdown
        from iclr2027.arr_adapter import packet_from_arr_artifacts
        from iclr2027.review_state import PrefixReviewState, parse_review_state
        from iclr2027.validators import gold_from_validation

        packet, _ = packet_from_arr_artifacts(
            Path(__file__).parent / "fixtures" / "iclr2027" / "native_summary.json",
            pnu="1168011800104170004",
            program="neighborhood",
            case_id="dev-template-accept-native",
        )
        gold = gold_from_validation(packet, mutation_family="")
        prompt = render_case_prompt(project_public_case(packet, _IDENTITY))
        template_json = prompt.split("ARCH_REVIEW_STATE\n```json\n", 1)[1].split(
            "\n```", 1
        )[0]
        model_state = json.loads(template_json)
        self.assertEqual(
            model_state["checked_domains"],
            ["site", "geometry", "law", "parking", "program"],
        )
        model_state.update(
            {
                "blocking_issue_codes": list(gold.blocking_issue_codes),
                "missing_evidence_codes": list(gold.missing_evidence_codes),
                "evidence_ids": list(gold.required_evidence_ids),
                "recommended_decision": gold.expected_decision,
                "confidence": 0.9,
            }
        )
        parsed = parse_review_state(
            "ARCH_REVIEW_STATE\n```json\n"
            + json.dumps(model_state)
            + "\n```"
        )
        prefix = PrefixReviewState(0, parsed.state, parsed.complete, parsed.error_codes)

        score = score_prefix(prefix, gold, packet)
        breakdown = score_prefix_breakdown(prefix, gold, packet)

        self.assertTrue(parsed.complete)
        self.assertEqual(gold.expected_decision, "STOP_ACCEPT")
        self.assertEqual(breakdown["decision_score"], 1.0)
        self.assertEqual(score.verdict_score, 1.0)

    def test_output_contract_is_repeated_after_the_evidence_packet(self) -> None:
        prompt = render_case_prompt(
            _public(
                _packet(
                    case_id="dev-contract-01",
                    pnu="1168011800104170004",
                )
            )
        )

        evidence_end = prompt.index("END_EVIDENCE_PACKET")
        contract_start = prompt.index("ARCH_REVIEW_STATE", evidence_end)
        self.assertGreater(contract_start, evidence_end)
        self.assertIn('"recommended_decision": "CONTINUE"', prompt[contract_start:])
        self.assertIn('"state_schema": "ARCH_REVIEW_STATE"', prompt[contract_start:])
        self.assertIn(
            "append it only after the complete fenced block",
            prompt[contract_start:],
        )
        self.assertIn("STOP_ACCEPT requires both issue lists to be empty", prompt)
        self.assertIn("CONTINUE requires missing evidence and no blocking issue", prompt)
        self.assertIn("STOP_REJECT requires at least one blocking issue", prompt)
        self.assertIn(
            "evidence:review_agent never substitutes for a missing domain record",
            prompt,
        )
        self.assertIn("law.required_evidence_missing", prompt)
        self.assertIn("parking.required_evidence_missing", prompt)
        self.assertIn(
            "Never place an evidence: identifier in either issue-code list",
            prompt,
        )
        self.assertIn(
            "missing_evidence_codes contains issue codes, not evidence IDs",
            prompt,
        )
        self.assertIn(
            "The ARCH_REVIEW_STATE block must be the first content in your response",
            prompt,
        )
        self.assertIn(
            "Its first line must be the literal text ARCH_REVIEW_STATE",
            prompt,
        )
        self.assertIn("at most three short bullets after the block", prompt)

    def test_policy_is_stage_aware_and_exposes_only_recomputed_attempt_integrity(self) -> None:
        manifest = {
            "schema_version": "ace.iclr2027.portfolio_attempt_identity.v2",
            "attempt_stage": "selection",
            "program": "neighborhood",
        }
        public_case = ArchitecturePublicCase(
            case_id="case:" + "1" * 64,
            site_ref="site:" + "2" * 64,
            program="neighborhood",
            execution_id=None,
            program_hash=None,
            geometry_hash=None,
            evidence=(
                {
                    "evidence_id": "evidence:portfolio_attempt",
                    "domain": "program",
                    "status": "failed",
                    "evidence": manifest,
                },
            ),
            subject_kind="portfolio_attempt",
            source_artifact_sha256="3" * 64,
            attempt_id="attempt:" + "4" * 64,
            attempt_hash="0" * 64,
            attempt_stage="selection",
        )

        prompt = render_case_prompt(public_case)

        self.assertIn('"portfolio_attempt_hash_matches":false', prompt)
        self.assertNotIn(sha256_json(manifest), prompt)
        self.assertIn("For subject_kind=portfolio_attempt", prompt)
        self.assertIn("selection.no_admitted_candidate", prompt)
        self.assertIn("materialization.no_candidate_reached_ledger", prompt)
        self.assertIn("preflight.program_site_infeasible", prompt)
        self.assertIn("candidate_floor_context.typed_ledger_missing", prompt)
        self.assertIn("For subject_kind=execution", prompt)
        self.assertIn("program.capacity_failed", prompt)
        self.assertIn("0.70", prompt)

    def test_prompt_recursively_excludes_private_identifiers_and_gold_labels(self) -> None:
        packet = _packet(
            case_id="dev-case-sensitive-01",
            pnu="1168011800104170004",
        )

        prompt = render_case_prompt(_public(packet))
        payload = _prompt_payload(packet)

        self.assertNotIn(packet.case_id, prompt)
        self.assertNotIn('"condition":', prompt)
        self.assertNotIn("expected_decision", prompt)
        self.assertNotIn("mutation_family", prompt)
        self.assertNotIn("gold_", prompt.lower())
        self.assertNotIn("case_ref", payload)
        self.assertIn("site_ref", payload)
        for item in _walk(payload):
            if isinstance(item, str):
                self.assertIsNone(_RAW_PNU.search(item), item)
            if isinstance(item, str) and item.lower() in {"case_id", "condition"}:
                self.fail(f"private key leaked recursively: {item}")

    def test_site_ref_is_deterministic_per_pnu_and_separates_sites(self) -> None:
        first = _prompt_payload(
            _packet(case_id="dev-case-01", pnu="1168011800104170004")
        )
        same_site = _prompt_payload(
            _packet(case_id="different-case-id", pnu="1168011800104170004")
        )
        different_site = _prompt_payload(
            _packet(case_id="dev-case-02", pnu="1111010100100000001")
        )

        self.assertEqual(first["site_ref"], same_site["site_ref"])
        self.assertNotEqual(first["site_ref"], different_site["site_ref"])
        self.assertRegex(first["site_ref"], r"^site:[0-9a-f]{64}$")

    def test_condition_does_not_mutate_nonprivate_evidence_text(self) -> None:
        evidence = (
            {
                "evidence_id": "evidence:program_agent",
                "capacity_alternative_id": "native-material-option",
                "description": "native stone alternative",
            },
        )

        def packet(condition: str) -> ArchitectureEvidencePacket:
            return ArchitectureEvidencePacket(
                case_id=f"dev-{condition}-01",
                pnu="1168011800104170004",
                program="neighborhood",
                condition=condition,  # type: ignore[arg-type]
                execution_id="execution-1",
                program_hash="a" * 64,
                geometry_hash="b" * 64,
                evidence=evidence,
            )

        native_payload = _prompt_payload(packet("native"))
        challenged_payload = _prompt_payload(packet("challenged"))

        self.assertEqual(native_payload, challenged_payload)
        self.assertEqual(native_payload["evidence"][0], evidence[0])
        self.assertIn("capacity_alternative_id", native_payload["evidence"][0])

    def test_case_id_redaction_does_not_replace_unrelated_substrings(self) -> None:
        packet = ArchitectureEvidencePacket(
            case_id="case",
            pnu="1168011800104170004",
            program="neighborhood",
            condition="native",
            execution_id="execution-1",
            program_hash="a" * 64,
            geometry_hash="b" * 64,
            evidence=(
                {
                    "evidence_id": "evidence:program_agent",
                    "showcase_id": "staircase",
                    "case_id": "case",
                },
            ),
        )

        payload = _prompt_payload(packet)

        self.assertEqual(payload["evidence"][0]["showcase_id"], "staircase")
        self.assertNotIn("case_id", payload["evidence"][0])


if __name__ == "__main__":
    unittest.main()
