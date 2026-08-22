from __future__ import annotations

import asyncio
import json
import unittest

from autogen_agentchat.messages import TextMessage


def _block(
    *,
    decision: str = "STOP_ACCEPT",
    evidence_ids: tuple[str, ...] = ("evidence:geometry_agent",),
) -> str:
    payload = {
        "checked_domains": ["geometry"],
        "blocking_issue_codes": (
            ["geometry.test_blocker"] if decision == "STOP_REJECT" else []
        ),
        "missing_evidence_codes": (
            ["law.required_evidence_missing"] if decision == "CONTINUE" else []
        ),
        "evidence_ids": list(evidence_ids),
        "recommended_decision": decision,
        "confidence": 0.9,
    }
    return "ARCH_REVIEW_STATE\n```json\n" + json.dumps(payload) + "\n```"


class ParseGatedSignalTerminationTests(unittest.TestCase):
    def _condition(
        self,
        *,
        signals: tuple[str, ...] = ("TERMINATE",),
        sources: tuple[str, ...] = ("review_agent",),
        allowed_evidence_ids: tuple[str, ...] = ("evidence:geometry_agent",),
        required_prior_sources: tuple[str, ...] = (),
    ):
        try:
            from iclr2027.termination import ParseGatedSignalTermination
        except ImportError as exc:
            self.fail(f"parse-gated termination is missing: {exc}")
        return ParseGatedSignalTermination(
            signals=signals,
            sources=sources,
            allowed_evidence_ids=allowed_evidence_ids,
            required_prior_sources=required_prior_sources,
        )

    def test_authorized_terminal_decision_with_exact_final_signal_stops(self) -> None:
        cases = (
            ("STOP_ACCEPT", "TERMINATE"),
            ("STOP_REJECT", "APPROVED"),
            ("STOP_ACCEPT", "VERDICT"),
            ("STOP_REJECT", "ANALYSIS_DONE"),
        )
        for decision, signal in cases:
            with self.subTest(decision=decision, signal=signal):
                condition = self._condition(signals=(signal,))
                message = TextMessage(
                    source="review_agent",
                    content=f"{_block(decision=decision)}\n{signal}",
                )

                result = asyncio.run(condition([message]))

                self.assertIsNotNone(result)

    def test_invalid_or_nonterminal_outputs_never_stop(self) -> None:
        markerless = _block().replace("ARCH_REVIEW_STATE\n", "", 1)
        malformed = "ARCH_REVIEW_STATE\n```json\n{bad json}\n```"
        samples = (
            markerless + "\nTERMINATE",
            malformed + "\nTERMINATE",
            _block(decision="CONTINUE") + "\nTERMINATE",
            _block(evidence_ids=("evidence:invented_agent",)) + "\nTERMINATE",
            _block(),
            _block() + "\nPlease do not TERMINATE yet.",
            _block() + "\nTERMINATE extra",
            "TERMINATE\n" + _block(),
        )
        for content in samples:
            with self.subTest(content=content[-40:]):
                condition = self._condition()

                result = asyncio.run(
                    condition([TextMessage(source="review_agent", content=content)])
                )

                self.assertIsNone(result)

    def test_specialist_cannot_stop_with_an_otherwise_valid_output(self) -> None:
        for source in ("geometry_agent", "compliance_agent", "law_agent"):
            with self.subTest(source=source):
                condition = self._condition()
                message = TextMessage(
                    source=source,
                    content=_block(decision="STOP_REJECT") + "\nTERMINATE",
                )

                result = asyncio.run(condition([message]))

                self.assertIsNone(result)

    def test_only_the_newest_chat_message_can_trigger_termination(self) -> None:
        condition = self._condition()
        messages = [
            TextMessage(
                source="review_agent",
                content=_block() + "\nTERMINATE",
            ),
            TextMessage(source="geometry_agent", content="continuing review"),
        ]

        result = asyncio.run(condition(messages))

        self.assertIsNone(result)

    def test_known_but_cross_case_evidence_cannot_trigger_termination(self) -> None:
        condition = self._condition(
            allowed_evidence_ids=("evidence:geometry_agent",),
        )
        message = TextMessage(
            source="review_agent",
            content=(
                _block(evidence_ids=("evidence:portfolio_attempt",))
                + "\nTERMINATE"
            ),
        )

        result = asyncio.run(condition([message]))

        self.assertIsNone(result)

    def test_reviewer_can_stop_only_after_each_required_specialist_spoke(self) -> None:
        condition = self._condition(
            required_prior_sources=("geometry_agent", "compliance_agent"),
        )
        reviewer = TextMessage(
            source="review_agent",
            content=_block() + "\nTERMINATE",
        )

        self.assertIsNone(asyncio.run(condition([reviewer])))
        self.assertIsNone(
            asyncio.run(
                condition(
                    [TextMessage(source="geometry_agent", content=_block())]
                )
            )
        )
        self.assertIsNone(asyncio.run(condition([reviewer])))
        self.assertIsNone(
            asyncio.run(
                condition(
                    [TextMessage(source="compliance_agent", content=_block())]
                )
            )
        )
        self.assertIsNotNone(asyncio.run(condition([reviewer])))


if __name__ == "__main__":
    unittest.main()
