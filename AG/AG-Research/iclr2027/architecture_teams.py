"""Architecture-specialized agents over the unchanged legacy topology family."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Mapping, Sequence
from typing import Any

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import Response
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.base import OrTerminationCondition
from autogen_agentchat.messages import HandoffMessage
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat, Swarm
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage, TextMessage
from autogen_core import CancellationToken

from config import PATTERN_MAX_MESSAGES, PATTERNS_ALL
from experiment_utils import MoATeam, PipelineTeam, _make_agent, _make_client

from .prompts import ArchitectureRole, ROLE_BANKS, architecture_system_prompt
from .termination import ParseGatedSignalTermination


_ALL_TYPED_EVIDENCE_IDS = (
    "evidence:site_agent",
    "evidence:geometry_agent",
    "evidence:law_graph_agent",
    "evidence:parking_agent",
    "evidence:program_agent",
    "evidence:review_agent",
    "evidence:portfolio_attempt",
)


class _CoverageHandoffAssistantAgent(AssistantAgent):
    """Emit one substantive review, then a deterministic sanitized handoff."""

    def __init__(self, *args: Any, coverage_handoff_target: str, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._coverage_handoff_target = coverage_handoff_target
        self._coverage_substantive_emitted = False
        self._coverage_handoff_emitted = False

    async def on_messages_stream(
        self,
        messages: Sequence[BaseChatMessage],
        cancellation_token: CancellationToken,
    ) -> AsyncGenerator[BaseAgentEvent | BaseChatMessage | Response, None]:
        if self._coverage_substantive_emitted and not self._coverage_handoff_emitted:
            self._coverage_handoff_emitted = True
            yield Response(
                chat_message=HandoffMessage(
                    source=self.name,
                    target=self._coverage_handoff_target,
                    content=f"Coverage handoff to {self._coverage_handoff_target}",
                )
            )
            return
        async for item in super().on_messages_stream(messages, cancellation_token):
            if (
                isinstance(item, Response)
                and isinstance(item.chat_message, TextMessage)
                and item.chat_message.content.strip()
            ):
                self._coverage_substantive_emitted = True
            yield item

    async def on_reset(self, cancellation_token: CancellationToken) -> None:
        await super().on_reset(cancellation_token)
        self._coverage_substantive_emitted = False
        self._coverage_handoff_emitted = False

    async def save_state(self) -> dict[str, Any]:
        state = dict(await super().save_state())
        state["coverage_handoff_state"] = {
            "schema_version": "ace.iclr2027.coverage_handoff_state.v1",
            "substantive_emitted": self._coverage_substantive_emitted,
            "handoff_emitted": self._coverage_handoff_emitted,
        }
        return state

    async def load_state(self, state: Mapping[str, Any]) -> None:
        payload = state.get("coverage_handoff_state")
        if not isinstance(payload, dict) or set(payload) != {
            "schema_version",
            "substantive_emitted",
            "handoff_emitted",
        }:
            raise ValueError("coverage handoff state is missing or invalid")
        if payload["schema_version"] != "ace.iclr2027.coverage_handoff_state.v1":
            raise ValueError("coverage handoff state schema is unsupported")
        substantive = payload["substantive_emitted"]
        handoff = payload["handoff_emitted"]
        if type(substantive) is not bool or type(handoff) is not bool:
            raise ValueError("coverage handoff flags must be boolean")
        if handoff and not substantive:
            raise ValueError("coverage handoff cannot precede substantive output")
        await super().load_state(
            {key: value for key, value in state.items() if key != "coverage_handoff_state"}
        )
        self._coverage_substantive_emitted = substantive
        self._coverage_handoff_emitted = handoff


def _agents(
    count: int,
    *,
    model: str | None,
    terminal_signal: str | None,
    coverage_handoffs: dict[str, str] | None = None,
) -> list[Any]:
    terminal_source = "architect_review_agent" if count == 1 else "review_agent"
    agents: list[Any] = []
    for role in ROLE_BANKS[count]:
        target = (coverage_handoffs or {}).get(role.name)
        system_prompt = architecture_system_prompt(
            role,
            terminal_signal=(terminal_signal if role.name == terminal_source else None),
            handoff_targets=(target,) if target else (),
        )
        if target:
            agents.append(
                _CoverageHandoffAssistantAgent(
                    role.name,
                    description=role.description,
                    system_message=system_prompt,
                    model_client=_make_client(model),
                    reflect_on_tool_use=False,
                    tool_call_summary_format="{result}",
                    coverage_handoff_target=target,
                )
            )
        else:
            agents.append(
                _make_agent(
                    role.name,
                    role.description,
                    system_prompt,
                    model=model,
                )
            )
    return agents


def _termination(
    max_messages: int,
    *signals: str,
    sources: tuple[str, ...],
    allowed_evidence_ids: tuple[str, ...],
    required_prior_sources: tuple[str, ...],
) -> OrTerminationCondition:
    return OrTerminationCondition(
        ParseGatedSignalTermination(
            signals=signals,
            sources=sources,
            allowed_evidence_ids=allowed_evidence_ids,
            required_prior_sources=required_prior_sources,
        ),
        MaxMessageTermination(max_messages=max_messages),
    )


def _selector_prompt() -> str:
    return (
        "Select the next architecture reviewer from {participants} using the role descriptions. "
        "The team controller guarantees one substantive turn from every role before free selection. "
        "Return only the role name.\n\n{roles}\n\n{history}"
    )


def _debate_selector_prompt() -> str:
    return (
        "Run an architecture evidence debate with claim, challenge, and judge phases. "
        "Use geometry_agent for measured claims, compliance_agent for challenges, "
        "and review_agent for the final judge state. The controller guarantees one "
        "substantive turn from every role before free selection. Return only the role "
        "name from {participants}.\n\n{roles}\n\n{history}"
    )


def _coverage_selector(
    participant_names: tuple[str, ...],
    max_messages: int,
):
    """Require one substantive TextMessage per role, then defer to the model."""

    def select(
        messages: Sequence[BaseAgentEvent | BaseChatMessage],
    ) -> str | None:
        observed = {
            message.source for message in messages if isinstance(message, TextMessage)
        }
        for participant_name in participant_names:
            if participant_name not in observed:
                return participant_name
        participant_turn_count = sum(
            isinstance(message, TextMessage)
            and message.source in participant_names
            for message in messages
        )
        if participant_turn_count >= max_messages - 2:
            return participant_names[-1]
        return None

    return select


def _specialist_sources(count: int) -> tuple[str, ...]:
    terminal_source = "architect_review_agent" if count == 1 else "review_agent"
    return tuple(
        role.name for role in ROLE_BANKS[count] if role.name != terminal_source
    )


class ArchitectureTeamFactory:
    """Build architecture roles while preserving each legacy team topology."""

    @staticmethod
    def build(
        pattern: str,
        max_messages: int | None = None,
        model: str | None = None,
        allowed_evidence_ids: tuple[str, ...] | None = None,
    ):
        if pattern not in PATTERNS_ALL:
            raise ValueError(f"Unknown pattern: {pattern}. Available: {PATTERNS_ALL}")
        mm = max_messages or PATTERN_MAX_MESSAGES.get(pattern, 10)
        evidence_ids = allowed_evidence_ids or _ALL_TYPED_EVIDENCE_IDS
        builders = {
            "solo": lambda: ArchitectureTeamFactory._round_robin(1, mm, model, evidence_ids),
            "rr2": lambda: ArchitectureTeamFactory._round_robin(2, mm, model, evidence_ids),
            "rr3": lambda: ArchitectureTeamFactory._round_robin(3, mm, model, evidence_ids),
            "rr4": lambda: ArchitectureTeamFactory._round_robin(4, mm, model, evidence_ids),
            "sel3": lambda: ArchitectureTeamFactory._selector(3, mm, model, evidence_ids),
            "sel4": lambda: ArchitectureTeamFactory._selector(4, mm, model, evidence_ids),
            "swm3": lambda: ArchitectureTeamFactory._swarm(3, mm, model, evidence_ids),
            "swm4": lambda: ArchitectureTeamFactory._swarm(4, mm, model, evidence_ids),
            "refl2": lambda: ArchitectureTeamFactory._reflection(2, mm, model, evidence_ids),
            "refl3": lambda: ArchitectureTeamFactory._reflection(3, mm, model, evidence_ids),
            "debate3": lambda: ArchitectureTeamFactory._debate(3, mm, model, evidence_ids),
            "debate4": lambda: ArchitectureTeamFactory._debate(4, mm, model, evidence_ids),
            "pipe": lambda: ArchitectureTeamFactory._pipeline(model, evidence_ids),
            "moa": lambda: ArchitectureTeamFactory._moa(model),
        }
        return builders[pattern]()

    @staticmethod
    def _round_robin(
        count: int,
        max_messages: int,
        model: str | None,
        allowed_evidence_ids: tuple[str, ...],
    ):
        return RoundRobinGroupChat(
            participants=_agents(
                count,
                model=model,
                terminal_signal="TERMINATE",
            ),
            termination_condition=_termination(
                max_messages,
                "TERMINATE",
                sources=(
                    "architect_review_agent" if count == 1 else "review_agent",
                ),
                allowed_evidence_ids=allowed_evidence_ids,
                required_prior_sources=_specialist_sources(count),
            ),
        )

    @staticmethod
    def _selector(
        count: int,
        max_messages: int,
        model: str | None,
        allowed_evidence_ids: tuple[str, ...],
    ):
        return SelectorGroupChat(
            participants=_agents(
                count,
                model=model,
                terminal_signal="TERMINATE",
            ),
            model_client=_make_client(model),
            termination_condition=_termination(
                max_messages,
                "TERMINATE",
                sources=("review_agent",),
                allowed_evidence_ids=allowed_evidence_ids,
                required_prior_sources=_specialist_sources(count),
            ),
            selector_prompt=_selector_prompt(),
            selector_func=_coverage_selector(
                tuple(role.name for role in ROLE_BANKS[count]),
                max_messages,
            ),
            allow_repeated_speaker=False,
        )

    @staticmethod
    def _swarm(
        count: int,
        max_messages: int,
        model: str | None,
        allowed_evidence_ids: tuple[str, ...],
    ):
        roles = ROLE_BANKS[count]
        coverage_handoffs = {
            role.name: roles[index + 1].name
            for index, role in enumerate(roles[:-1])
        }
        return Swarm(
            participants=_agents(
                count,
                model=model,
                terminal_signal="TERMINATE",
                coverage_handoffs=coverage_handoffs,
            ),
            termination_condition=_termination(
                max_messages,
                "TERMINATE",
                sources=("review_agent",),
                allowed_evidence_ids=allowed_evidence_ids,
                required_prior_sources=_specialist_sources(count),
            ),
        )

    @staticmethod
    def _reflection(
        count: int,
        max_messages: int,
        model: str | None,
        allowed_evidence_ids: tuple[str, ...],
    ):
        return RoundRobinGroupChat(
            participants=_agents(
                count,
                model=model,
                terminal_signal="APPROVED",
            ),
            termination_condition=_termination(
                max_messages,
                "APPROVED",
                "TERMINATE",
                sources=("review_agent",),
                allowed_evidence_ids=allowed_evidence_ids,
                required_prior_sources=_specialist_sources(count),
            ),
        )

    @staticmethod
    def _debate(
        count: int,
        max_messages: int,
        model: str | None,
        allowed_evidence_ids: tuple[str, ...],
    ):
        return SelectorGroupChat(
            participants=_agents(
                count,
                model=model,
                terminal_signal="TERMINATE",
            ),
            model_client=_make_client(model),
            termination_condition=_termination(
                max_messages,
                "TERMINATE",
                sources=("review_agent",),
                allowed_evidence_ids=allowed_evidence_ids,
                required_prior_sources=_specialist_sources(count),
            ),
            selector_prompt=_debate_selector_prompt(),
            selector_func=_coverage_selector(
                tuple(role.name for role in ROLE_BANKS[count]),
                max_messages,
            ),
            allow_repeated_speaker=False,
        )

    @staticmethod
    def _pipeline(model: str | None, allowed_evidence_ids: tuple[str, ...]):
        stage1 = SelectorGroupChat(
            participants=_agents(
                3,
                model=model,
                terminal_signal="ANALYSIS_DONE",
            ),
            model_client=_make_client(model),
            termination_condition=_termination(
                8,
                "ANALYSIS_DONE",
                sources=("review_agent",),
                allowed_evidence_ids=allowed_evidence_ids,
                required_prior_sources=_specialist_sources(3),
            ),
            selector_prompt=_selector_prompt(),
            allow_repeated_speaker=False,
        )
        stage2 = RoundRobinGroupChat(
            participants=_agents(
                2,
                model=model,
                terminal_signal="TERMINATE",
            ),
            termination_condition=_termination(
                6,
                "TERMINATE",
                sources=("review_agent",),
                allowed_evidence_ids=allowed_evidence_ids,
                required_prior_sources=_specialist_sources(2),
            ),
        )
        return PipelineTeam(stage1=stage1, stage2=stage2)

    @staticmethod
    def _moa(model: str | None):
        roles = ROLE_BANKS[4]
        proposers = [
            _make_agent(
                role.name,
                role.description,
                architecture_system_prompt(role, terminal_signal=None),
                model=model,
            )
            for role in roles[:3]
        ]
        reviewer: ArchitectureRole = roles[-1]
        aggregator = _make_agent(
            reviewer.name,
            reviewer.description,
            architecture_system_prompt(reviewer, terminal_signal=None),
            model=model,
        )
        return MoATeam(
            proposers=proposers,
            aggregator=aggregator,
            max_proposer_messages=3,
        )
