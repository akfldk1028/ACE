# LLM Architect Agent Memory

Created: 2026-07-07

Reason:

- The MAAS system already used OpenAI-backed LLM proposals in `design.maas.llm_proposals`.
- However, the LLM role was outside the MAAS agent graph, so the AG-light/JSON_MODULES flow made it look like `parking_agent -> massdsl_agent` happened without an explicit LLM architectural-language owner.
- This caused a misleading architecture: agents existed, but the LLM proposal stage was an orphan module.

Current contract:

- `llm_architect_agent` owns LLM-authored architectural language review.
- `massdsl_agent` owns MassDSL contract validation.
- `maas_geometry_agent` owns source geometry/materialization.
- `law_graph_agent` and `parking_agent` remain hard-gate evidence providers.

Reference structures:

- GitAgent repo-style modular agent identity:
  `agent.yaml`, `SOUL.md`, `RULES.md`, `memory/`.
- OpenAI Agents SDK-style concepts:
  named agents, handoffs, tools, guardrails, tracing.

