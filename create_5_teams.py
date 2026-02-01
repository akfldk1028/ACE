#!/usr/bin/env python3
"""
Create 5 multi-agent teams in AutoGen Studio via POST /api/teams/
"""
import json
import urllib.request

BASE_URL = "http://localhost:8081/api/teams/"
USER_ID = "admin"

# ── Reusable building blocks ──────────────────────────────────────────

def model_client():
    return {
        "provider": "autogen_ext.models.openai.OpenAIChatCompletionClient",
        "component_type": "model",
        "version": 1,
        "component_version": 1,
        "description": "Chat completion client for OpenAI hosted models.",
        "label": "OpenAIChatCompletionClient",
        "config": {"model": "gpt-4o-mini"}
    }

def model_context():
    return {
        "provider": "autogen_core.model_context.UnboundedChatCompletionContext",
        "component_type": "chat_completion_context",
        "version": 1,
        "component_version": 1,
        "description": "An unbounded chat completion context that keeps a view of the all the messages.",
        "label": "UnboundedChatCompletionContext",
        "config": {}
    }

def agent(name, description, system_message, handoffs=None):
    cfg = {
        "name": name,
        "model_client": model_client(),
        "model_context": model_context(),
        "description": description,
        "system_message": system_message,
        "model_client_stream": False,
        "reflect_on_tool_use": False,
        "tool_call_summary_format": "{result}",
        "metadata": {}
    }
    if handoffs is not None:
        cfg["handoffs"] = handoffs
    return {
        "provider": "autogen_agentchat.agents.AssistantAgent",
        "component_type": "agent",
        "version": 2,
        "component_version": 2,
        "description": description,
        "label": "AssistantAgent",
        "config": cfg
    }

def termination(text_mention="TERMINATE", max_messages=10):
    return {
        "provider": "autogen_agentchat.base.OrTerminationCondition",
        "component_type": "termination",
        "version": 1,
        "component_version": 1,
        "label": "OrTerminationCondition",
        "config": {
            "conditions": [
                {
                    "provider": "autogen_agentchat.conditions.TextMentionTermination",
                    "component_type": "termination",
                    "version": 1,
                    "component_version": 1,
                    "description": "Terminate the conversation if a specific text is mentioned.",
                    "label": "TextMentionTermination",
                    "config": {"text": text_mention}
                },
                {
                    "provider": "autogen_agentchat.conditions.MaxMessageTermination",
                    "component_type": "termination",
                    "version": 1,
                    "component_version": 1,
                    "description": "Terminate the conversation after a maximum number of messages have been exchanged.",
                    "label": "MaxMessageTermination",
                    "config": {"max_messages": max_messages, "include_agent_event": False}
                }
            ]
        }
    }


# ── Team 1: Full-Stack Dev Pipeline (RoundRobinGroupChat) ────────────

team1 = {
    "provider": "autogen_agentchat.teams.RoundRobinGroupChat",
    "component_type": "team",
    "version": 1,
    "component_version": 1,
    "description": "Full-Stack Dev Pipeline: Sequential planner -> coder -> reviewer -> deployer workflow for end-to-end software development.",
    "label": "Full-Stack Dev Pipeline",
    "config": {
        "name": "full_stack_dev_pipeline",
        "description": "Sequential pipeline for full-stack software development with planning, coding, review, and deployment stages.",
        "participants": [
            agent("planner_agent",
                  "Analyzes requirements and creates architecture plan",
                  "You are a senior software architect. Analyze the given requirements thoroughly and create a detailed architecture plan including: tech stack choices, component breakdown, data flow, API design, and implementation steps. Be specific and actionable. Pass your plan to the coder for implementation."),
            agent("coder_agent",
                  "Implements code based on the architecture plan",
                  "You are an expert full-stack developer. Based on the architecture plan provided by the planner, implement clean, well-structured code. Include proper error handling, type annotations, and follow best practices. Provide complete, runnable code with clear comments."),
            agent("reviewer_agent",
                  "Reviews code for bugs, security issues, and performance",
                  "You are a senior code reviewer specializing in security and performance. Review the code for: bugs, security vulnerabilities (OWASP Top 10), performance bottlenecks, code quality, and best practices. Provide specific, actionable feedback with line references."),
            agent("deployer_agent",
                  "Creates deployment configuration and finalizes",
                  "You are a DevOps engineer. Create deployment configuration including: Dockerfile, docker-compose.yml, CI/CD pipeline config, environment variables, and monitoring setup. Summarize the entire development pipeline output. When your deployment config is complete, say TERMINATE."),
        ],
        "termination_condition": termination("TERMINATE", 20),
        "emit_team_events": False
    }
}

# ── Team 2: Knowledge Research Hub (SelectorGroupChat) ────────────────

team2 = {
    "provider": "autogen_agentchat.teams.SelectorGroupChat",
    "component_type": "team",
    "version": 1,
    "component_version": 1,
    "description": "Knowledge Research Hub: Dynamic expert routing for multi-domain questions spanning history, philosophy, science, math, and literature.",
    "label": "Knowledge Research Hub",
    "config": {
        "name": "knowledge_research_hub",
        "description": "A selector-based team that routes questions to the most relevant domain expert.",
        "participants": [
            agent("coordinator",
                  "Coordinates research across domain experts",
                  "You are a research coordinator. Analyze the user's question, identify which domain expert(s) should respond, and synthesize their answers into a comprehensive response. When the question is fully answered with expert input, say TERMINATE."),
            agent("history_expert",
                  "Expert in world history, civilizations, and historical events",
                  "You are a world-class historian. Provide detailed, accurate answers about historical events, civilizations, figures, and their significance. Cite specific dates, places, and primary sources when possible."),
            agent("philosophy_expert",
                  "Expert in philosophy, ethics, and critical thinking",
                  "You are a philosophy professor. Provide deep philosophical analysis including relevant theories, thinkers, and schools of thought. Address both Western and Eastern philosophical traditions."),
            agent("science_expert",
                  "Expert in natural sciences, physics, chemistry, biology",
                  "You are a research scientist. Provide accurate scientific explanations with current understanding. Include relevant theories, experiments, and empirical evidence. Simplify complex concepts when needed."),
            agent("math_expert",
                  "Expert in mathematics, statistics, and computation",
                  "You are a mathematician. Provide clear mathematical explanations with step-by-step solutions. Use proper notation and explain the intuition behind formulas and proofs."),
            agent("literature_expert",
                  "Expert in literature, literary analysis, and creative writing",
                  "You are a literature professor. Provide insightful literary analysis including themes, symbolism, historical context, and comparative analysis across works and traditions."),
        ],
        "model_client": model_client(),
        "termination_condition": termination("TERMINATE", 15),
        "selector_prompt": """You are the team coordinator. Analyze the current conversation and determine which agent should speak next.

Available agents:
- coordinator: Routes tasks and synthesizes final answers. Select when the question needs initial analysis or when enough expert input has been gathered for a final summary.
- history_expert: Select for questions about historical events, civilizations, wars, historical figures, timelines.
- philosophy_expert: Select for questions about philosophical concepts, ethics, morality, existence, logic, reasoning.
- science_expert: Select for questions about physics, chemistry, biology, astronomy, natural phenomena.
- math_expert: Select for questions about mathematics, statistics, equations, proofs, computation.
- literature_expert: Select for questions about books, poetry, literary analysis, authors, literary movements.

Select the agent whose expertise best matches the current question or discussion point. If the question spans multiple domains, prioritize the most relevant expert first.""",
        "allow_repeated_speaker": False,
        "emit_team_events": False
    }
}

# ── Team 3: Creative Arts Workshop (RoundRobinGroupChat) ──────────────

team3 = {
    "provider": "autogen_agentchat.teams.RoundRobinGroupChat",
    "component_type": "team",
    "version": 1,
    "component_version": 1,
    "description": "Creative Arts Workshop: Sequential creative flow from poetry to philosophical depth, historical context, and critical evaluation.",
    "label": "Creative Arts Workshop",
    "config": {
        "name": "creative_arts_workshop",
        "description": "A round-robin creative team that produces rich, multi-layered creative works.",
        "participants": [
            agent("poet",
                  "Creates poetry and creative writing based on themes",
                  "You are an acclaimed poet and creative writer. Given a theme or prompt, create beautiful, evocative poetry or creative prose. Use vivid imagery, metaphor, and rhythm. Experiment with form and structure. Your writing should stir emotions and provoke thought."),
            agent("philosopher",
                  "Adds philosophical depth and meaning to creative works",
                  "You are a philosopher who finds deep meaning in art. Take the creative work produced and add philosophical depth: explore the existential themes, the human condition, and universal truths embedded in the work. Draw connections to great philosophical traditions."),
            agent("historian",
                  "Adds historical context and cultural references",
                  "You are a cultural historian. Enrich the creative work with historical context: identify parallels to historical events, cultural movements, and artistic traditions. Add references that deepen the work's resonance and place it within the broader tapestry of human expression."),
            agent("critic",
                  "Evaluates creative work and provides constructive feedback",
                  "You are a distinguished literary critic. Evaluate the collaborative creative work holistically: assess its artistic merit, coherence, emotional impact, and intellectual depth. Provide constructive suggestions for improvement. When your evaluation is complete, say TERMINATE."),
        ],
        "termination_condition": termination("TERMINATE", 12),
        "emit_team_events": False
    }
}

# ── Team 4: Code Quality Gate (Swarm with handoffs) ──────────────────

team4 = {
    "provider": "autogen_agentchat.teams.Swarm",
    "component_type": "team",
    "version": 1,
    "component_version": 1,
    "description": "Code Quality Gate: Swarm-based code review with specialized handoffs between triage, security, performance, style reviewers, and summary.",
    "label": "Code Quality Gate",
    "config": {
        "name": "code_quality_gate",
        "description": "A swarm team for comprehensive code quality review with specialized handoffs.",
        "participants": [
            agent("triage_agent",
                  "Receives code and triages to appropriate reviewers",
                  "You are a code review triage agent. When you receive code to review:\n1. First, hand off to security_reviewer for security analysis.\n2. After security review returns, hand off to performance_reviewer.\n3. After performance review returns, hand off to style_reviewer.\n4. After all reviews complete, hand off to summary_agent for final summary.\nUse the transfer functions to hand off to the appropriate reviewer.",
                  handoffs=["security_reviewer", "performance_reviewer", "style_reviewer", "summary_agent"]),
            agent("security_reviewer",
                  "Reviews code for security vulnerabilities (OWASP)",
                  "You are a security expert. Analyze the code for OWASP Top 10 vulnerabilities including: injection flaws, broken authentication, sensitive data exposure, XXE, broken access control, security misconfiguration, XSS, insecure deserialization, using components with known vulnerabilities, and insufficient logging. Provide severity ratings and remediation steps. When done, transfer back to triage_agent.",
                  handoffs=["triage_agent"]),
            agent("performance_reviewer",
                  "Reviews code for performance issues",
                  "You are a performance engineer. Analyze the code for: algorithmic complexity issues, memory leaks, unnecessary allocations, N+1 query problems, missing caching opportunities, inefficient data structures, and concurrency issues. Suggest optimizations with benchmarking advice. When done, transfer back to triage_agent.",
                  handoffs=["triage_agent"]),
            agent("style_reviewer",
                  "Reviews code style and best practices",
                  "You are a code style expert. Review the code for: naming conventions, code organization, SOLID principles, DRY violations, documentation quality, test coverage gaps, and adherence to language-specific idioms. Suggest improvements following industry best practices. When done, transfer back to triage_agent.",
                  handoffs=["triage_agent"]),
            agent("summary_agent",
                  "Summarizes all code reviews into a final report",
                  "You are a technical lead. Compile all review findings from the security, performance, and style reviewers into a comprehensive code quality report. Prioritize issues by severity, provide an overall quality score, and list actionable next steps. When your summary is complete, say TERMINATE.",
                  handoffs=[]),
        ],
        "termination_condition": termination("TERMINATE", 15),
        "emit_team_events": False
    }
}

# ── Team 5: All-Agent Orchestrator (SelectorGroupChat) ───────────────

team5 = {
    "provider": "autogen_agentchat.teams.SelectorGroupChat",
    "component_type": "team",
    "version": 1,
    "component_version": 1,
    "description": "All-Agent Orchestrator: Master orchestrator with specialists for development, research, creative, math, DevOps, and legal tasks.",
    "label": "All-Agent Orchestrator",
    "config": {
        "name": "all_agent_orchestrator",
        "description": "A master orchestrator team that routes any task to the appropriate specialist agent.",
        "participants": [
            agent("orchestrator",
                  "Master orchestrator that routes tasks to specialists and synthesizes results",
                  "You are the master orchestrator. Analyze each task and determine which specialist should handle it. After specialists provide their input, synthesize the results into a coherent final answer. For complex tasks, coordinate multiple specialists. When the task is fully resolved, say TERMINATE."),
            agent("dev_agent",
                  "Software development specialist for coding tasks",
                  "You are a senior full-stack developer. Handle all software development tasks including: writing code, debugging, architecture design, API development, database design, and technical documentation. Provide production-ready solutions with best practices."),
            agent("research_agent",
                  "Research specialist for information gathering and analysis",
                  "You are a research analyst. Handle research tasks including: information synthesis, fact-checking, comparative analysis, trend analysis, and literature review. Provide well-sourced, comprehensive answers with clear methodology."),
            agent("creative_agent",
                  "Creative specialist for writing, arts, and content",
                  "You are a creative professional. Handle creative tasks including: copywriting, poetry, storytelling, content strategy, branding, and artistic direction. Produce engaging, original content that resonates with the target audience."),
            agent("math_agent",
                  "Mathematics specialist for computation and analysis",
                  "You are a mathematician and data scientist. Handle mathematical tasks including: calculations, statistical analysis, modeling, optimization, probability, and data interpretation. Show your work step by step with clear explanations."),
            agent("ops_agent",
                  "DevOps specialist for deployment and infrastructure",
                  "You are a DevOps/SRE engineer. Handle operational tasks including: CI/CD pipelines, containerization, cloud infrastructure, monitoring, alerting, scaling, and incident response. Provide production-grade configurations and runbooks."),
            agent("legal_agent",
                  "Legal specialist for compliance and regulatory tasks",
                  "You are a legal analyst. Handle legal tasks including: regulatory compliance review, contract analysis, privacy policy assessment (GDPR, CCPA), licensing, and intellectual property guidance. Provide clear legal analysis with actionable recommendations. Note: this is informational only, not legal advice."),
        ],
        "model_client": model_client(),
        "termination_condition": termination("TERMINATE", 25),
        "selector_prompt": """You are the task routing coordinator. Analyze the current conversation and determine which agent should speak next.

Available agents:
- orchestrator: Select when the task needs initial analysis, multi-domain coordination, or when enough specialist input has been gathered for a final synthesis.
- dev_agent: Select for software development, coding, debugging, API design, database tasks, technical architecture.
- research_agent: Select for research, information gathering, fact-checking, comparative analysis, literature review.
- creative_agent: Select for creative writing, poetry, content creation, branding, storytelling, artistic tasks.
- math_agent: Select for mathematics, statistics, computation, data analysis, optimization, probability.
- ops_agent: Select for DevOps, deployment, CI/CD, infrastructure, monitoring, cloud operations, scaling.
- legal_agent: Select for legal questions, compliance, contracts, privacy, licensing, regulatory matters.

Select the agent whose expertise best matches the current task or discussion point. For multi-domain tasks, the orchestrator should coordinate between specialists.""",
        "allow_repeated_speaker": False,
        "emit_team_events": False
    }
}

# ── Send requests ─────────────────────────────────────────────────────

teams = [
    ("Team 1: Full-Stack Dev Pipeline", team1),
    ("Team 2: Knowledge Research Hub", team2),
    ("Team 3: Creative Arts Workshop", team3),
    ("Team 4: Code Quality Gate", team4),
    ("Team 5: All-Agent Orchestrator", team5),
]

print("=" * 70)
print("Creating 5 Multi-Agent Teams in AutoGen Studio")
print("=" * 70)

for label, team_component in teams:
    payload = {
        "user_id": USER_ID,
        "component": team_component
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BASE_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            body = json.loads(resp.read().decode("utf-8"))
            team_id = body.get("data", {}).get("id", "N/A")
            print(f"\n[OK] {label}")
            print(f"     Status: {status}")
            print(f"     Team ID: {team_id}")
            print(f"     Label: {team_component['label']}")
            print(f"     Provider: {team_component['provider']}")
            agents = [p['config']['name'] for p in team_component['config']['participants']]
            print(f"     Agents: {', '.join(agents)}")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"\n[FAIL] {label}")
        print(f"     Status: {e.code}")
        print(f"     Error: {err_body}")
    except Exception as e:
        print(f"\n[FAIL] {label}")
        print(f"     Error: {e}")

print("\n" + "=" * 70)
print("Done!")
print("=" * 70)
