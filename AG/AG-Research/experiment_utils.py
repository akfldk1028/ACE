"""
Shared infrastructure for multi-agent termination experiments.

Components:
  A. TurnRecord / RunResult (dataclasses)
  B. TeamFactory (13-pattern builder)
  C. ComposedTeam wrappers (Pipeline, MoA)
  D. ExperimentRunner (single + batch execution)
  E. I/O helpers (CSV, JSON, task loading)
"""

import asyncio
import csv
import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import Handoff, TaskResult
from autogen_agentchat.conditions import (
    MaxMessageTermination,
    TextMentionTermination,
)
from autogen_agentchat.base import OrTerminationCondition
from autogen_agentchat.teams import (
    RoundRobinGroupChat,
    SelectorGroupChat,
    Swarm,
)

from config import (
    MODEL,
    MODEL_SELECTOR,
    PATTERN_AGENT_COUNT,
    PATTERN_CATEGORY,
    PATTERN_MAX_MESSAGES,
    PATTERNS_ALL,
)

# Import model client
from AG_Cohub.model_factory import ClaudeCLIChatCompletionClient


# ========================================
# A. Data Classes
# ========================================


@dataclass
class TurnRecord:
    index: int
    source: str
    content: str
    timestamp: str
    tokens_in: int = 0
    tokens_out: int = 0


@dataclass
class RunResult:
    experiment_id: str
    task_id: str
    pattern: str
    repeat_index: int
    pattern_category: str
    agent_count: int
    stop_reason: str | None
    duration_sec: float
    total_tokens_in: int
    total_tokens_out: int
    total_tokens: int
    turn_count: int
    agent_turn_count: int
    terminated_by: str | None
    turns: list[TurnRecord] = field(default_factory=list)
    error: str | None = None
    quality_score: float | None = None
    converged_at: int | None = None
    stage_results: list[Any] | None = None  # Pipeline/MoA sub-results


# ========================================
# B. TeamFactory - 13 Pattern Builder
# ========================================


def _make_client(model: str | None = None):
    """Create model client. Claude (default), OpenAI (gpt-*), xAI (grok-*), or Google (gemini-*)."""
    if model is None:
        import config
        model = config.MODEL
    if "gpt" in model.lower() or "o1" in model.lower() or "o3" in model.lower():
        from autogen_ext.models.openai import OpenAIChatCompletionClient
        import os
        kwargs = {"model": model, "api_key": os.environ.get("OPENAI_API_KEY")}
        # GPT-5.4 and other new models need explicit model_info
        if "5.4" in model or "5-4" in model:
            kwargs["model_info"] = {"vision": False, "function_calling": True, "json_output": True, "family": "gpt-5"}
        return OpenAIChatCompletionClient(**kwargs)
    if "grok" in model.lower():
        from autogen_ext.models.openai import OpenAIChatCompletionClient
        import os
        return OpenAIChatCompletionClient(
            model=model,
            api_key=os.environ.get("XAI_API_KEY"),
            base_url="https://api.x.ai/v1",
            model_info={"vision": False, "function_calling": True, "json_output": True, "family": "unknown"},
        )
    if "gemini" in model.lower():
        from autogen_ext.models.openai import OpenAIChatCompletionClient
        import os
        return OpenAIChatCompletionClient(
            model=model,
            api_key=os.environ.get("GOOGLE_GEMINI_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            model_info={"vision": False, "function_calling": True, "json_output": True, "family": "unknown"},
        )
    return ClaudeCLIChatCompletionClient(
        model=model,
        agent_config={"profile": "text_only", "max_turns": 1},
    )


def _make_agent(
    name: str,
    description: str,
    system_message: str,
    model: str | None = None,
    handoffs: list[Handoff] | None = None,
) -> AssistantAgent:
    """Create an AssistantAgent with standard settings."""
    kwargs: dict[str, Any] = {
        "name": name,
        "description": description,
        "system_message": system_message,
        "model_client": _make_client(model),
        "reflect_on_tool_use": False,
        "tool_call_summary_format": "{result}",
    }
    if handoffs:
        kwargs["handoffs"] = handoffs
    return AssistantAgent(**kwargs)


class TeamFactory:
    """Build any of the 13 team patterns."""

    @staticmethod
    def build(pattern: str, max_messages: int | None = None):
        """Build a team for the given pattern ID.

        Returns a team object (GroupChat/Swarm) or a ComposedTeam (Pipeline/MoA).
        """
        if pattern not in PATTERNS_ALL:
            raise ValueError(f"Unknown pattern: {pattern}. Available: {PATTERNS_ALL}")

        mm = max_messages or PATTERN_MAX_MESSAGES.get(pattern, 10)

        builders = {
            "solo": lambda: TeamFactory._build_solo(mm),
            "rr2": lambda: TeamFactory._build_rr(2, mm),
            "rr3": lambda: TeamFactory._build_rr(3, mm),
            "rr4": lambda: TeamFactory._build_rr(4, mm),
            "sel3": lambda: TeamFactory._build_selector(3, mm),
            "sel4": lambda: TeamFactory._build_selector(4, mm),
            "swm3": lambda: TeamFactory._build_swarm(3, mm),
            "swm4": lambda: TeamFactory._build_swarm(4, mm),
            "refl2": lambda: TeamFactory._build_reflection(2, mm),
            "refl3": lambda: TeamFactory._build_reflection(3, mm),
            "debate3": lambda: TeamFactory._build_debate(3, mm),
            "debate4": lambda: TeamFactory._build_debate(4, mm),
            "pipe": lambda: TeamFactory._build_pipeline(mm),
            "moa": lambda: TeamFactory._build_moa(mm),
        }
        return builders[pattern]()

    # ---- Category S: Single-Agent Baseline ----

    @staticmethod
    def _build_solo(max_messages: int):
        """Single agent baseline — one general-purpose agent."""
        agent = _make_agent(
            "solo_agent",
            "General-purpose assistant",
            "You are a knowledgeable assistant. Answer the given question thoroughly and concisely. "
            "When your answer is complete, end with TERMINATE.",
        )
        termination = OrTerminationCondition(
            TextMentionTermination(text="TERMINATE"),
            MaxMessageTermination(max_messages=max_messages),
        )
        return RoundRobinGroupChat(
            participants=[agent],
            termination_condition=termination,
        )

    # ---- Category A: Flat Sequential ----

    @staticmethod
    def _build_rr(n_agents: int, max_messages: int):
        """RoundRobin with 2/3/4 agents."""
        agents_spec = {
            2: [
                ("researcher", "Research and analysis specialist",
                 "You are a researcher. Investigate the given topic and provide key facts and analysis."),
                ("writer", "Writer and synthesizer",
                 "You are a writer. Based on the research, compose a clear and comprehensive answer. "
                 "When the answer is complete and sufficient, end with TERMINATE."),
            ],
            3: [
                ("researcher", "Research specialist",
                 "You are a researcher. Investigate the topic and organize key facts and arguments."),
                ("writer", "Content writer",
                 "You are a writer. Based on the research, compose a structured answer."),
                ("reviewer", "Quality reviewer",
                 "You are a reviewer. Evaluate the answer for accuracy and completeness. "
                 "If sufficient, say TERMINATE. If not, suggest specific improvements."),
            ],
            4: [
                ("researcher", "Information gatherer",
                 "You are a researcher. Collect key facts, data, and examples about the topic."),
                ("analyst", "Analysis specialist",
                 "You are an analyst. Analyze the collected information and organize it logically."),
                ("writer", "Content writer",
                 "You are a writer. Based on the analysis, compose a comprehensive answer."),
                ("reviewer", "Quality reviewer",
                 "You are a reviewer. Check accuracy, completeness, and coherence. "
                 "If sufficient, say TERMINATE. If not, point out specific issues."),
            ],
        }

        agents = [
            _make_agent(name, desc, sys_msg)
            for name, desc, sys_msg in agents_spec[n_agents]
        ]

        termination = OrTerminationCondition(
            TextMentionTermination(text="TERMINATE"),
            MaxMessageTermination(max_messages=max_messages),
        )

        return RoundRobinGroupChat(
            participants=agents,
            termination_condition=termination,
        )

    # ---- Category B: Dynamic Routing ----

    @staticmethod
    def _build_selector(n_agents: int, max_messages: int):
        """SelectorGroupChat with 3/4 agents."""
        agents_spec = {
            3: [
                ("expert_a", "Technical analysis expert",
                 "You are a technical expert. Analyze from a technical perspective."),
                ("expert_b", "Business and strategy expert",
                 "You are a business expert. Analyze from a business/market perspective."),
                ("expert_c", "Synthesis and conclusion expert",
                 "You are a synthesis expert. Combine analyses into a final conclusion. "
                 "When sufficient, say TERMINATE."),
            ],
            4: [
                ("expert_a", "Technical analysis expert",
                 "You are a technical expert. Analyze from a technical perspective."),
                ("expert_b", "Business and strategy expert",
                 "You are a business expert. Analyze from a business/market perspective."),
                ("expert_c", "Creative and alternative expert",
                 "You are a creative thinker. Propose alternative approaches and novel perspectives."),
                ("expert_d", "Synthesis and conclusion expert",
                 "You are a synthesis expert. Combine all analyses into a final conclusion. "
                 "When sufficient, say TERMINATE."),
            ],
        }

        agents = [
            _make_agent(name, desc, sys_msg)
            for name, desc, sys_msg in agents_spec[n_agents]
        ]

        import config as _cfg
        selector_client = _make_client(_cfg.MODEL_SELECTOR)

        names = ", ".join(a.name for a in agents)
        selector_prompt = (
            "You are in a role play game. The following roles are available:\n{roles}.\n"
            "Read the following conversation. Then select the next role from {participants} to play. "
            "Only return the role name.\n\n{history}\n\n"
            "Read the above conversation. Then select the next role from {participants} to play. "
            "Only return the role name."
        )

        termination = OrTerminationCondition(
            TextMentionTermination(text="TERMINATE"),
            MaxMessageTermination(max_messages=max_messages),
        )

        return SelectorGroupChat(
            participants=agents,
            model_client=selector_client,
            termination_condition=termination,
            selector_prompt=selector_prompt,
            allow_repeated_speaker=False,
        )

    @staticmethod
    def _build_swarm(n_agents: int, max_messages: int):
        """Swarm with 3/4 agents using handoffs."""
        if n_agents == 3:
            triage = _make_agent(
                "triage", "Initial triage and routing",
                "You are a triage agent. Analyze the task and delegate to the right specialist. "
                "Use handoff to transfer to specialist_a (technical) or specialist_b (synthesis).",
                handoffs=[
                    Handoff(target="specialist_a", description="Transfer to technical specialist"),
                    Handoff(target="specialist_b", description="Transfer to synthesis specialist"),
                ],
            )
            specialist_a = _make_agent(
                "specialist_a", "Technical specialist",
                "You are a technical specialist. Provide technical analysis. "
                "When done, hand off back to triage for next steps.",
                handoffs=[
                    Handoff(target="triage", description="Return to triage"),
                ],
            )
            specialist_b = _make_agent(
                "specialist_b", "Synthesis specialist",
                "You are a synthesis specialist. Produce the final comprehensive answer. "
                "When complete, say TERMINATE.",
                handoffs=[
                    Handoff(target="triage", description="Return to triage if more work needed"),
                ],
            )
            agents = [triage, specialist_a, specialist_b]

        else:  # n_agents == 4
            triage = _make_agent(
                "triage", "Initial triage and routing",
                "You are a triage agent. Analyze the task and delegate to specialists. "
                "Use handoffs: specialist_a (technical), specialist_b (analysis), specialist_c (QA).",
                handoffs=[
                    Handoff(target="specialist_a", description="Transfer to technical specialist"),
                    Handoff(target="specialist_b", description="Transfer to analysis specialist"),
                    Handoff(target="specialist_c", description="Transfer to QA specialist"),
                ],
            )
            specialist_a = _make_agent(
                "specialist_a", "Technical specialist",
                "You are a technical specialist. Provide technical analysis. "
                "Hand off to triage or specialist_c when done.",
                handoffs=[
                    Handoff(target="triage", description="Return to triage"),
                    Handoff(target="specialist_c", description="Send to QA for review"),
                ],
            )
            specialist_b = _make_agent(
                "specialist_b", "Analysis specialist",
                "You are an analysis specialist. Provide structured analysis. "
                "Hand off back to triage when done.",
                handoffs=[
                    Handoff(target="triage", description="Return to triage"),
                ],
            )
            specialist_c = _make_agent(
                "specialist_c", "QA and conclusion specialist",
                "You are a QA specialist. Review and finalize the answer. "
                "When quality is sufficient, say TERMINATE.",
                handoffs=[
                    Handoff(target="triage", description="Return to triage if needs more work"),
                ],
            )
            agents = [triage, specialist_a, specialist_b, specialist_c]

        termination = OrTerminationCondition(
            TextMentionTermination(text="TERMINATE"),
            MaxMessageTermination(max_messages=max_messages),
        )

        return Swarm(
            participants=agents,
            termination_condition=termination,
        )

    # ---- Category C: Structured Feedback ----

    @staticmethod
    def _build_reflection(n_agents: int, max_messages: int):
        """Reflection pattern with 2/3 agents (feedback loop)."""
        agents_spec = {
            2: [
                ("generator", "Content generator",
                 "You are a content generator. Create or improve the answer based on the task. "
                 "If the critic provided feedback, incorporate it into your revision."),
                ("critic", "Quality critic",
                 "You are a quality critic. Review the generator's output carefully. "
                 "Provide specific, actionable feedback for improvement. "
                 "If the quality is sufficient and no major issues remain, say APPROVED."),
            ],
            3: [
                ("generator", "Initial draft generator",
                 "You are a draft generator. Create the initial answer or revise based on feedback."),
                ("critic", "Critical reviewer",
                 "You are a critic. Analyze the draft and provide specific improvement suggestions."),
                ("editor", "Final editor and approver",
                 "You are an editor. Incorporate the critic's feedback into a polished version. "
                 "If quality is sufficient, say APPROVED. Otherwise, note remaining issues."),
            ],
        }

        agents = [
            _make_agent(name, desc, sys_msg)
            for name, desc, sys_msg in agents_spec[n_agents]
        ]

        termination = OrTerminationCondition(
            TextMentionTermination(text="APPROVED"),
            TextMentionTermination(text="TERMINATE"),
            MaxMessageTermination(max_messages=max_messages),
        )

        return RoundRobinGroupChat(
            participants=agents,
            termination_condition=termination,
        )

    @staticmethod
    def _build_debate(n_agents: int, max_messages: int):
        """Debate pattern with 3/4 agents (SelectorGroupChat)."""
        if n_agents == 3:
            agents_list = [
                ("advocate", "Proponent of the proposal",
                 "You are an advocate. Present strong arguments in favor. "
                 "Highlight benefits, opportunities, and supporting evidence."),
                ("critic", "Critical opponent",
                 "You are a critic. Present counterarguments and identify weaknesses. "
                 "Highlight risks, costs, and potential problems."),
                ("judge", "Impartial judge",
                 "You are a judge. After hearing both sides, deliver a balanced verdict. "
                 "When ready, state your conclusion starting with VERDICT:"),
            ]
        else:  # n_agents == 4
            agents_list = [
                ("advocate", "Proponent of the proposal",
                 "You are an advocate. Present strong arguments in favor."),
                ("critic", "Critical opponent",
                 "You are a critic. Present counterarguments and identify weaknesses."),
                ("moderator", "Debate moderator",
                 "You are a moderator. Summarize key points, identify gaps in the debate, "
                 "and guide the discussion. When both sides have been heard, invite the judge."),
                ("judge", "Impartial judge",
                 "You are a judge. After hearing the moderated debate, deliver a balanced verdict. "
                 "State your conclusion starting with VERDICT:"),
            ]

        agents = [
            _make_agent(name, desc, sys_msg)
            for name, desc, sys_msg in agents_list
        ]

        import config as _cfg
        selector_client = _make_client(_cfg.MODEL_SELECTOR)

        if n_agents == 3:
            selector_prompt = (
                "You are in a role play game. The following roles are available:\n{roles}.\n"
                "Read the following conversation. Rules:\n"
                "1. advocate and critic should alternate (2-3 turns each)\n"
                "2. After sufficient debate, judge delivers the final verdict\n"
                "Select the next role from {participants}. Only return the role name.\n\n"
                "{history}\n\n"
                "Select the next role from {participants}. Only return the role name."
            )
        else:
            selector_prompt = (
                "You are in a role play game. The following roles are available:\n{roles}.\n"
                "Read the following conversation. Rules:\n"
                "1. advocate and critic alternate arguments\n"
                "2. moderator periodically summarizes and guides\n"
                "3. After sufficient debate, judge delivers the final verdict\n"
                "Select the next role from {participants}. Only return the role name.\n\n"
                "{history}\n\n"
                "Select the next role from {participants}. Only return the role name."
            )

        termination = OrTerminationCondition(
            TextMentionTermination(text="VERDICT"),
            TextMentionTermination(text="TERMINATE"),
            MaxMessageTermination(max_messages=max_messages),
        )

        return SelectorGroupChat(
            participants=agents,
            model_client=selector_client,
            termination_condition=termination,
            selector_prompt=selector_prompt,
            allow_repeated_speaker=False,
        )

    # ---- Category D: Composed/Nested ----

    @staticmethod
    def _build_pipeline(max_messages: int):
        """Pipeline: Stage1 (Selector 3) -> Stage2 (RoundRobin 2)."""
        import config as _cfg
        # Stage 1: Analysis team (SelectorGroupChat, 3 agents)
        stage1_agents = [
            _make_agent("analyst_tech", "Technical analyst",
                        "You are a technical analyst. Analyze from a technical perspective."),
            _make_agent("analyst_biz", "Business analyst",
                        "You are a business analyst. Analyze from a business/market perspective."),
            _make_agent("analyst_lead", "Lead analyst",
                        "You are the lead analyst. Synthesize both analyses. "
                        "When analysis is complete, say ANALYSIS_DONE."),
        ]

        stage1_termination = OrTerminationCondition(
            TextMentionTermination(text="ANALYSIS_DONE"),
            MaxMessageTermination(max_messages=8),
        )

        stage1 = SelectorGroupChat(
            participants=stage1_agents,
            model_client=_make_client(_cfg.MODEL_SELECTOR),
            termination_condition=stage1_termination,
            allow_repeated_speaker=False,
        )

        # Stage 2: Synthesis team (RoundRobinGroupChat, 2 agents)
        stage2_agents = [
            _make_agent("synthesizer", "Content synthesizer",
                        "You are a synthesizer. Based on the analysis provided, "
                        "compose a structured and comprehensive final answer."),
            _make_agent("finalizer", "Final reviewer",
                        "You are a finalizer. Review and polish the answer. "
                        "When complete, say TERMINATE."),
        ]

        stage2_termination = OrTerminationCondition(
            TextMentionTermination(text="TERMINATE"),
            MaxMessageTermination(max_messages=6),
        )

        stage2 = RoundRobinGroupChat(
            participants=stage2_agents,
            termination_condition=stage2_termination,
        )

        return PipelineTeam(stage1=stage1, stage2=stage2)

    @staticmethod
    def _build_moa(max_messages: int):
        """Mixture of Agents: 3 parallel proposers -> 1 aggregator."""
        proposers = [
            _make_agent("proposer_a", "Technical/factual perspective",
                        "You are an expert providing a technical, factual analysis. "
                        "Give a complete, self-contained answer in one response."),
            _make_agent("proposer_b", "Critical/risk perspective",
                        "You are a critical analyst. Identify weaknesses, risks, and counterarguments. "
                        "Give a complete, self-contained answer in one response."),
            _make_agent("proposer_c", "Creative/alternative perspective",
                        "You are a creative thinker. Propose novel approaches and alternative viewpoints. "
                        "Give a complete, self-contained answer in one response."),
        ]

        aggregator = _make_agent(
            "aggregator", "Final aggregator",
            "You are a synthesis expert. You will receive perspectives from three experts. "
            "Combine their insights into a balanced, comprehensive final answer.",
        )

        return MoATeam(proposers=proposers, aggregator=aggregator, max_proposer_messages=3)


# ========================================
# C. ComposedTeam Wrappers
# ========================================


def _extract_final_message(result: TaskResult) -> str:
    """Extract the last non-empty message text from a TaskResult."""
    for msg in reversed(result.messages):
        text = str(msg.content).strip()
        if text:
            return text
    return ""


def _collect_turns(result: TaskResult) -> list[TurnRecord]:
    """Convert TaskResult messages to TurnRecord list."""
    turns = []
    for i, msg in enumerate(result.messages):
        usage = getattr(msg, "models_usage", None)
        turns.append(TurnRecord(
            index=i,
            source=getattr(msg, "source", "unknown"),
            content=str(msg.content)[:2000],
            timestamp=datetime.now(timezone.utc).isoformat(),
            tokens_in=usage.prompt_tokens if usage else 0,
            tokens_out=usage.completion_tokens if usage else 0,
        ))
    return turns


class PipelineTeam:
    """Two-stage pipeline: stage1.run() -> stage2.run(stage1_output)."""

    def __init__(self, stage1, stage2):
        self.stage1 = stage1
        self.stage2 = stage2
        self._is_composed = True

    async def run(self, task: str) -> TaskResult:
        """Run both stages sequentially."""
        self._stage1_result = await self.stage1.run(task=task)
        stage1_text = _extract_final_message(self._stage1_result)

        stage2_task = (
            f"Based on the following analysis, compose a comprehensive final answer:\n\n"
            f"{stage1_text}"
        )
        self._stage2_result = await self.stage2.run(task=stage2_task)

        # Combine messages for unified result
        all_messages = list(self._stage1_result.messages) + list(self._stage2_result.messages)
        return TaskResult(
            messages=all_messages,
            stop_reason=self._stage2_result.stop_reason,
        )

    async def reset(self):
        """Reset both stages."""
        if hasattr(self.stage1, "reset"):
            await self.stage1.reset()
        if hasattr(self.stage2, "reset"):
            await self.stage2.reset()


class MoATeam:
    """Mixture of Agents: N proposers in parallel -> 1 aggregator."""

    def __init__(self, proposers: list[AssistantAgent], aggregator: AssistantAgent,
                 max_proposer_messages: int = 3):
        self.proposers = proposers
        self.aggregator = aggregator
        self.max_proposer_messages = max_proposer_messages
        self._is_composed = True
        self._proposer_results: list[TaskResult] = []

    async def _run_single_proposer(self, agent: AssistantAgent, task: str) -> TaskResult:
        """Run a single proposer as a one-agent RoundRobin team."""
        termination = MaxMessageTermination(max_messages=self.max_proposer_messages)
        team = RoundRobinGroupChat(
            participants=[agent],
            termination_condition=termination,
        )
        result = await team.run(task=task)
        return result

    async def run(self, task: str) -> TaskResult:
        """Run all proposers in parallel, then aggregate."""
        # Layer 1: parallel proposers
        self._proposer_results = await asyncio.gather(*[
            self._run_single_proposer(p, task)
            for p in self.proposers
        ])

        # Extract each proposer's final text
        texts = [_extract_final_message(r) for r in self._proposer_results]
        combined = "\n\n---\n\n".join(
            f"[{self.proposers[i].name}]:\n{texts[i]}"
            for i in range(len(texts))
        )

        # Layer 2: aggregator
        agg_task = (
            f"Three experts provided their perspectives. "
            f"Synthesize them into a balanced final answer:\n\n{combined}"
        )
        agg_termination = MaxMessageTermination(max_messages=2)
        agg_team = RoundRobinGroupChat(
            participants=[self.aggregator],
            termination_condition=agg_termination,
        )
        self._agg_result = await agg_team.run(task=agg_task)

        # Combine all messages
        all_messages = []
        for r in self._proposer_results:
            all_messages.extend(r.messages)
        all_messages.extend(self._agg_result.messages)

        return TaskResult(
            messages=all_messages,
            stop_reason=self._agg_result.stop_reason,
        )

    async def reset(self):
        """Reset is handled by creating new teams each run."""
        pass


# ========================================
# D. ExperimentRunner
# ========================================


class ExperimentRunner:
    """Execute experiments and collect metrics."""

    @staticmethod
    async def run_single(
        team,
        task_text: str,
        experiment_id: str,
        task_id: str,
        pattern: str,
        repeat_index: int = 0,
    ) -> RunResult:
        """Run a single team execution and collect metrics."""
        t0 = time.monotonic()
        error = None
        result = None

        try:
            result = await team.run(task=task_text)
        except Exception as e:
            error = f"{type(e).__name__}: {str(e)[:500]}"

        duration = time.monotonic() - t0

        # Parse results
        turns: list[TurnRecord] = []
        stop_reason = None
        agent_sources: set[str] = set()

        if result:
            stop_reason = result.stop_reason
            turns = _collect_turns(result)
            for msg in result.messages:
                source = getattr(msg, "source", "unknown")
                if source != "user":
                    agent_sources.add(source)

        total_tokens_in = sum(t.tokens_in for t in turns)
        total_tokens_out = sum(t.tokens_out for t in turns)
        total_tokens = total_tokens_in + total_tokens_out

        # Determine terminator
        terminated_by = None
        if stop_reason:
            sr = str(stop_reason).lower()
            if "terminate" in sr or "approved" in sr or "verdict" in sr or "analysis_done" in sr:
                terminated_by = "keyword"
            elif "max" in sr:
                terminated_by = "max_messages"

        # For composed teams, collect stage results
        stage_results = None
        if hasattr(team, '_is_composed'):
            stage_results = []
            if isinstance(team, PipelineTeam):
                if hasattr(team, '_stage1_result') and team._stage1_result:
                    stage_results.append({
                        "stage": "stage1",
                        "turns": len(team._stage1_result.messages),
                        "stop_reason": team._stage1_result.stop_reason,
                    })
                if hasattr(team, '_stage2_result') and team._stage2_result:
                    stage_results.append({
                        "stage": "stage2",
                        "turns": len(team._stage2_result.messages),
                        "stop_reason": team._stage2_result.stop_reason,
                    })
            elif isinstance(team, MoATeam):
                for i, pr in enumerate(getattr(team, '_proposer_results', [])):
                    stage_results.append({
                        "stage": f"proposer_{i}",
                        "turns": len(pr.messages),
                        "stop_reason": pr.stop_reason,
                    })
                if hasattr(team, '_agg_result') and team._agg_result:
                    stage_results.append({
                        "stage": "aggregator",
                        "turns": len(team._agg_result.messages),
                        "stop_reason": team._agg_result.stop_reason,
                    })

        return RunResult(
            experiment_id=experiment_id,
            task_id=task_id,
            pattern=pattern,
            repeat_index=repeat_index,
            pattern_category=PATTERN_CATEGORY.get(pattern, "?"),
            agent_count=PATTERN_AGENT_COUNT.get(pattern, 0),
            stop_reason=stop_reason,
            duration_sec=round(duration, 2),
            total_tokens_in=total_tokens_in,
            total_tokens_out=total_tokens_out,
            total_tokens=total_tokens,
            turn_count=len(turns),
            agent_turn_count=len([t for t in turns if t.source != "user"]),
            terminated_by=terminated_by,
            turns=turns,
            error=error,
            stage_results=stage_results,
        )

    @staticmethod
    async def run_batch(
        patterns: list[str],
        tasks: list[dict],
        experiment_id: str,
        repeats: int = 1,
        max_messages: int | None = None,
        progress_callback=None,
        checkpoint_dir: Path | None = None,
    ) -> list[RunResult]:
        """Run all pattern × task × repeat combinations sequentially.

        If checkpoint_dir is provided, saves intermediate results after each
        pattern completes AND resumes from checkpoint on restart.
        """
        results = []
        done_keys: set[tuple[str, str, int]] = set()

        # Resume from checkpoint if exists
        if checkpoint_dir:
            ckpt = checkpoint_dir / "checkpoint.json"
            if ckpt.exists():
                import json as _json
                with open(ckpt, encoding="utf-8") as f:
                    prev = _json.load(f)
                for r in prev:
                    done_keys.add((r["pattern"], r["task_id"], r.get("repeat_index", 0)))
                results = [RunResult(**r) if isinstance(r, dict) else r for r in prev]
                print(f"  [resume] Loaded {len(results)} previous results from checkpoint")

        total = len(patterns) * len(tasks) * repeats
        done = len(results)

        for pattern in patterns:
            for task_meta in tasks:
                for rep in range(repeats):
                    key = (pattern, task_meta["id"], rep)
                    if key in done_keys:
                        continue  # Skip already completed runs

                    team = TeamFactory.build(pattern, max_messages=max_messages)

                    if progress_callback:
                        progress_callback(done, total, pattern, task_meta["id"], rep)

                    run_result = await ExperimentRunner.run_single(
                        team=team,
                        task_text=task_meta["task"],
                        experiment_id=experiment_id,
                        task_id=task_meta["id"],
                        pattern=pattern,
                        repeat_index=rep,
                    )
                    results.append(run_result)
                    done += 1

                    # Reset team for next run
                    if hasattr(team, "reset"):
                        try:
                            await team.reset()
                        except Exception:
                            pass

            # Checkpoint after each pattern completes
            if checkpoint_dir:
                checkpoint_dir.mkdir(parents=True, exist_ok=True)
                save_results_json(results, checkpoint_dir / "checkpoint.json")
                print(f"  [checkpoint] {len(results)} results saved after pattern={pattern}", flush=True)

        return results


# ========================================
# E. I/O Helpers
# ========================================


def load_tasks(path: str | Path | None = None) -> list[dict]:
    """Load task suite from JSON file."""
    if path is None:
        path = Path(__file__).parent / "task_suite.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_results_csv(results: list[RunResult], path: str | Path):
    """Save results summary to CSV (without turns)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "experiment_id", "task_id", "pattern", "repeat_index",
        "pattern_category", "agent_count",
        "stop_reason", "duration_sec",
        "total_tokens_in", "total_tokens_out", "total_tokens",
        "turn_count", "agent_turn_count", "terminated_by",
        "error", "quality_score", "converged_at",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            row = {k: getattr(r, k) for k in fieldnames}
            writer.writerow(row)


def save_results_json(results: list[RunResult], path: str | Path):
    """Save full results with turns to JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = []
    for r in results:
        d = asdict(r)
        data.append(d)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
