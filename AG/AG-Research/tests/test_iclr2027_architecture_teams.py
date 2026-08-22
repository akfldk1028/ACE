from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from autogen_agentchat.base import Response
from autogen_agentchat.messages import HandoffMessage, TextMessage
from autogen_core import CancellationToken


_VALID_TERMINAL_BLOCK = """ARCH_REVIEW_STATE
```json
{"checked_domains":["geometry"],"blocking_issue_codes":[],"missing_evidence_codes":[],"evidence_ids":["evidence:geometry_agent"],"recommended_decision":"STOP_ACCEPT","confidence":0.9}
```"""


def _teams(team: object) -> list[object]:
    if hasattr(team, "stage1") and hasattr(team, "stage2"):
        return [team.stage1, team.stage2]
    return [team]


def _participant_names(team: object) -> tuple[str, ...]:
    if hasattr(team, "stage1") and hasattr(team, "stage2"):
        return _participant_names(team.stage1) + _participant_names(team.stage2)
    if hasattr(team, "_participants"):
        return tuple(agent.name for agent in team._participants)
    if hasattr(team, "proposers"):
        return tuple(agent.name for agent in team.proposers) + (team.aggregator.name,)
    return ()


def _max_message_budgets(team: object) -> tuple[int, ...]:
    budgets: list[int] = []
    if hasattr(team, "max_proposer_messages"):
        budgets.append(int(team.max_proposer_messages))
        budgets.append(2)
        return tuple(budgets)
    for stage in _teams(team):
        condition = getattr(stage, "_termination_condition", None)
        for child in getattr(condition, "_conditions", (condition,)):
            if hasattr(child, "_max_messages"):
                budgets.append(int(child._max_messages))
    return tuple(budgets)


class ArchitectureTeamFactoryTests(unittest.TestCase):
    def test_all_topologies_preserve_type_participants_stages_and_budgets(self) -> None:
        try:
            from iclr2027.architecture_teams import ArchitectureTeamFactory
        except (ImportError, ModuleNotFoundError) as exc:
            self.fail(f"architecture team factory is missing: {exc}")
        from config import PATTERNS_ALL
        from experiment_utils import TeamFactory

        for pattern in PATTERNS_ALL:
            with self.subTest(pattern=pattern):
                legacy = TeamFactory.build(pattern, max_messages=11)
                architecture = ArchitectureTeamFactory.build(pattern, max_messages=11)
                self.assertEqual(
                    tuple(type(stage).__name__ for stage in _teams(architecture)),
                    tuple(type(stage).__name__ for stage in _teams(legacy)),
                )
                self.assertEqual(
                    len(_participant_names(architecture)),
                    len(_participant_names(legacy)),
                )
                self.assertEqual(len(_teams(architecture)), len(_teams(legacy)))
                self.assertEqual(
                    _max_message_budgets(architecture),
                    _max_message_budgets(legacy),
                )

    def test_three_agent_patterns_share_one_architecture_role_bank(self) -> None:
        from iclr2027.architecture_teams import ArchitectureTeamFactory

        patterns = ("rr3", "sel3", "swm3", "refl3", "debate3")
        names = {
            pattern: _participant_names(ArchitectureTeamFactory.build(pattern))
            for pattern in patterns
        }

        self.assertEqual(len(set(names.values())), 1)
        self.assertEqual(
            next(iter(names.values())),
            ("geometry_agent", "compliance_agent", "review_agent"),
        )

    def test_selector_patterns_force_one_substantive_turn_per_role_before_free_choice(self) -> None:
        from iclr2027.architecture_teams import ArchitectureTeamFactory

        history = []
        for pattern in ("sel3", "debate3"):
            with self.subTest(pattern=pattern):
                team = ArchitectureTeamFactory.build(pattern)
                selector = team._selector_func
                self.assertIsNotNone(selector)
                self.assertEqual(selector(history), "geometry_agent")
                with_geometry = [
                    TextMessage(source="geometry_agent", content=_VALID_TERMINAL_BLOCK)
                ]
                self.assertEqual(selector(with_geometry), "compliance_agent")
                with_compliance = with_geometry + [
                    TextMessage(source="compliance_agent", content=_VALID_TERMINAL_BLOCK)
                ]
                self.assertEqual(selector(with_compliance), "review_agent")
                with_all = with_compliance + [
                    TextMessage(source="review_agent", content=_VALID_TERMINAL_BLOCK)
                ]
                self.assertIsNone(selector(with_all))
                near_budget = with_all + [
                    TextMessage(source="geometry_agent", content=_VALID_TERMINAL_BLOCK),
                    TextMessage(source="compliance_agent", content=_VALID_TERMINAL_BLOCK),
                    TextMessage(source="review_agent", content=_VALID_TERMINAL_BLOCK),
                    TextMessage(source="geometry_agent", content=_VALID_TERMINAL_BLOCK),
                    TextMessage(source="compliance_agent", content=_VALID_TERMINAL_BLOCK),
                ]
                self.assertEqual(selector(near_budget), "review_agent")

    def test_debate_uses_claim_challenge_judge_prompt_and_standard_terminal_signal(self) -> None:
        from iclr2027.architecture_teams import ArchitectureTeamFactory

        team = ArchitectureTeamFactory.build("debate3")
        self.assertIn("claim, challenge, and judge", team._selector_prompt)
        reviewer = next(
            agent for agent in team._participants if agent.name == "review_agent"
        )
        prompt = "\n".join(message.content for message in reviewer._system_messages)
        self.assertIn("append TERMINATE", prompt)
        self.assertNotIn("append VERDICT", prompt)

    def test_swarm_has_directed_coverage_handoffs_and_explicit_two_turn_protocol(self) -> None:
        from iclr2027.architecture_teams import ArchitectureTeamFactory

        team = ArchitectureTeamFactory.build("swm3")
        agents = {agent.name: agent for agent in team._participants}
        expected_targets = {
            "geometry_agent": "compliance_agent",
            "compliance_agent": "review_agent",
            "review_agent": None,
        }
        for name, expected in expected_targets.items():
            with self.subTest(agent=name):
                self.assertEqual(
                    getattr(agents[name], "_coverage_handoff_target", None),
                    expected,
                )
                prompt = "\n".join(
                    message.content for message in agents[name]._system_messages
                )
                if expected:
                    self.assertIn("SWARM HANDOFF PROTOCOL", prompt)
                    self.assertIn("first activation", prompt)
                    self.assertIn(expected, prompt)

    def test_swarm_specialist_second_activation_emits_deterministic_handoff(self) -> None:
        from iclr2027.architecture_teams import ArchitectureTeamFactory

        team = ArchitectureTeamFactory.build("swm3")
        geometry = next(
            agent for agent in team._participants if agent.name == "geometry_agent"
        )
        geometry._coverage_substantive_emitted = True

        async def collect() -> list[object]:
            return [
                item
                async for item in geometry.on_messages_stream(
                    [], CancellationToken()
                )
            ]

        emitted = asyncio.run(collect())
        self.assertEqual(len(emitted), 1)
        self.assertIsInstance(emitted[0], Response)
        self.assertIsInstance(emitted[0].chat_message, HandoffMessage)
        self.assertEqual(emitted[0].chat_message.source, "geometry_agent")
        self.assertEqual(emitted[0].chat_message.target, "compliance_agent")

    def test_swarm_coverage_state_survives_agent_state_round_trip(self) -> None:
        from iclr2027.architecture_teams import ArchitectureTeamFactory

        source_team = ArchitectureTeamFactory.build("swm3")
        source = next(
            agent
            for agent in source_team._participants
            if agent.name == "geometry_agent"
        )
        source._coverage_substantive_emitted = True
        state = asyncio.run(source.save_state())

        restored_team = ArchitectureTeamFactory.build("swm3")
        restored = next(
            agent
            for agent in restored_team._participants
            if agent.name == "geometry_agent"
        )
        asyncio.run(restored.load_state(state))

        self.assertTrue(restored._coverage_substantive_emitted)
        self.assertFalse(restored._coverage_handoff_emitted)

    def test_every_agent_prompt_requires_structured_review_state(self) -> None:
        from config import PATTERNS_ALL
        from iclr2027.architecture_teams import ArchitectureTeamFactory

        for pattern in PATTERNS_ALL:
            team = ArchitectureTeamFactory.build(pattern)
            agents = []
            for stage in _teams(team):
                agents.extend(getattr(stage, "_participants", ()))
            agents.extend(getattr(team, "proposers", ()))
            if hasattr(team, "aggregator"):
                agents.append(team.aggregator)
            for agent in agents:
                with self.subTest(pattern=pattern, agent=agent.name):
                    prompt = "\n".join(message.content for message in agent._system_messages)
                    self.assertIn("ARCH_REVIEW_STATE", prompt)
                    self.assertIn("exactly one", prompt)

    def test_only_designated_reviewers_receive_terminal_signal_instructions(self) -> None:
        from config import PATTERNS_ALL
        from iclr2027.architecture_teams import ArchitectureTeamFactory

        for pattern in PATTERNS_ALL:
            team = ArchitectureTeamFactory.build(pattern)
            agents = []
            for stage in _teams(team):
                agents.extend(getattr(stage, "_participants", ()))
            agents.extend(getattr(team, "proposers", ()))
            if hasattr(team, "aggregator"):
                agents.append(team.aggregator)
            authorized = (
                set()
                if pattern == "moa"
                else {"architect_review_agent"}
                if pattern == "solo"
                else {"review_agent"}
            )
            for agent in agents:
                with self.subTest(pattern=pattern, agent=agent.name):
                    prompt = "\n".join(
                        message.content for message in agent._system_messages
                    )
                    if agent.name in authorized:
                        self.assertIn("After the block, append", prompt)
                        self.assertIn("You MUST append", prompt)
                        self.assertIn("Do not append it for CONTINUE", prompt)
                    else:
                        self.assertIn(
                            "Do not append a termination keyword",
                            prompt,
                        )

    def test_pilot_topologies_accept_only_parse_valid_reviewer_signals(self) -> None:
        from iclr2027.architecture_teams import ArchitectureTeamFactory

        cases = (
            ("solo", 0, "architect_review_agent", "TERMINATE"),
            ("rr3", 0, "review_agent", "TERMINATE"),
            ("sel3", 0, "review_agent", "TERMINATE"),
            ("swm3", 0, "review_agent", "TERMINATE"),
            ("refl3", 0, "review_agent", "APPROVED"),
            ("debate3", 0, "review_agent", "TERMINATE"),
            ("pipe", 0, "review_agent", "ANALYSIS_DONE"),
            ("pipe", 1, "review_agent", "TERMINATE"),
        )
        for pattern, stage_index, reviewer, signal in cases:
            with self.subTest(
                pattern=pattern,
                stage_index=stage_index,
                signal=signal,
            ):
                team = ArchitectureTeamFactory.build(pattern)
                stage = _teams(team)[stage_index]
                condition = stage._termination_condition
                specialist = TextMessage(
                    source="geometry_agent",
                    content=f"{_VALID_TERMINAL_BLOCK}\n{signal}",
                )

                premature = asyncio.run(condition([specialist]))

                self.assertIsNone(premature)
                for source in (
                    name for name in _participant_names(stage) if name != reviewer
                ):
                    observed = asyncio.run(
                        condition(
                            [
                                TextMessage(
                                    source=source,
                                    content=_VALID_TERMINAL_BLOCK,
                                )
                            ]
                        )
                    )
                    self.assertIsNone(observed)
                terminal = asyncio.run(
                    condition(
                        [
                            TextMessage(
                                source=reviewer,
                                content=f"{_VALID_TERMINAL_BLOCK}\n{signal}",
                            )
                        ]
                    )
                )
                self.assertIsNotNone(terminal)

    def test_max_message_termination_remains_a_fail_safe(self) -> None:
        from iclr2027.architecture_teams import ArchitectureTeamFactory

        team = ArchitectureTeamFactory.build("rr3", max_messages=1)
        markerless = _VALID_TERMINAL_BLOCK.replace("ARCH_REVIEW_STATE\n", "", 1)

        result = asyncio.run(
            team._termination_condition(
                [
                    TextMessage(
                        source="geometry_agent",
                        content=markerless + "\nTERMINATE",
                    )
                ]
            )
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.source, "MaxMessageTermination")

    def test_runner_uses_injected_builder_and_keeps_legacy_default(self) -> None:
        from experiment_utils import ExperimentRunner, RunResult, TeamFactory

        class FakeTeam:
            async def reset(self) -> None:
                return None

        fake_result = RunResult(
            experiment_id="exp",
            task_id="case",
            pattern="rr2",
            repeat_index=0,
            pattern_category="flat",
            agent_count=2,
            stop_reason="max",
            duration_sec=0.0,
            total_tokens_in=0,
            total_tokens_out=0,
            total_tokens=0,
            turn_count=0,
            agent_turn_count=0,
            terminated_by="max_messages",
        )
        calls: list[tuple[str, int | None]] = []

        def injected(pattern: str, max_messages: int | None) -> FakeTeam:
            calls.append((pattern, max_messages))
            return FakeTeam()

        async_mock = AsyncMock(return_value=fake_result)
        with patch.object(ExperimentRunner, "run_single", async_mock):
            asyncio.run(
                ExperimentRunner.run_batch(
                    patterns=["rr2"],
                    tasks=[{"id": "case", "task": "packet"}],
                    experiment_id="exp",
                    max_messages=7,
                    team_builder=injected,
                )
            )
        self.assertEqual(calls, [("rr2", 7)])

        with (
            patch.object(TeamFactory, "build", return_value=FakeTeam()) as legacy_build,
            patch.object(ExperimentRunner, "run_single", AsyncMock(return_value=fake_result)),
        ):
            asyncio.run(
                ExperimentRunner.run_batch(
                    patterns=["rr2"],
                    tasks=[{"id": "case", "task": "packet"}],
                    experiment_id="exp",
                    max_messages=7,
                )
            )
        legacy_build.assert_called_once_with("rr2", max_messages=7)

    def test_architecture_run_can_preserve_state_block_after_2000_characters(self) -> None:
        from autogen_agentchat.base import TaskResult
        from autogen_agentchat.messages import TextMessage
        from experiment_utils import ExperimentRunner

        class LongMessageTeam:
            async def run(self, task: str) -> TaskResult:
                content = "analysis " * 300 + "ARCH_REVIEW_STATE\n```json\n{}\n```"
                return TaskResult(
                    messages=[TextMessage(content=content, source="review_agent")],
                    stop_reason="max_messages",
                )

        full = asyncio.run(
            ExperimentRunner.run_single(
                team=LongMessageTeam(),
                task_text="packet",
                experiment_id="exp08",
                task_id="case",
                pattern="rr3",
                repeat_index=0,
                turn_content_limit=None,
            )
        )

        self.assertIn("ARCH_REVIEW_STATE", full.turns[0].content)
        self.assertGreater(len(full.turns[0].content), 2000)

    def test_structured_state_stop_reason_has_explicit_provenance(self) -> None:
        from autogen_agentchat.base import TaskResult
        from autogen_agentchat.messages import TextMessage
        from experiment_utils import ExperimentRunner

        class StructuredStopTeam:
            async def run(self, task: str) -> TaskResult:
                return TaskResult(
                    messages=[TextMessage(content=_VALID_TERMINAL_BLOCK, source="review_agent")],
                    stop_reason="Parse-valid terminal architecture review state received",
                )

        result = asyncio.run(
            ExperimentRunner.run_single(
                team=StructuredStopTeam(),
                task_text="packet",
                experiment_id="exp08",
                task_id="case",
                pattern="rr3",
                repeat_index=0,
            )
        )

        self.assertEqual(result.terminated_by, "structured_state")

    def test_substantive_turn_collection_excludes_swarm_control_events(self) -> None:
        from autogen_agentchat.base import TaskResult
        from autogen_agentchat.messages import HandoffMessage, TextMessage
        from experiment_utils import _collect_turns

        result = TaskResult(
            messages=[
                TextMessage(content="public packet", source="user"),
                TextMessage(content="ARCH_REVIEW_STATE", source="geometry_agent"),
                HandoffMessage(
                    content="Transferred to compliance_agent",
                    source="geometry_agent",
                    target="compliance_agent",
                ),
            ],
            stop_reason="max_messages",
        )

        turns = _collect_turns(
            result,
            content_limit=None,
            substantive_only=True,
        )

        self.assertEqual([turn.source for turn in turns], ["user", "geometry_agent"])


if __name__ == "__main__":
    unittest.main()
