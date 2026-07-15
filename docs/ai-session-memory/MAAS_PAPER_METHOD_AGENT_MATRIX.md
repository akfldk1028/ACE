# MAAS Paper Method to Agent Matrix

Updated: 2026-07-07

This file maps the paper/reference-code method to the MAAS agent modules. It exists to prevent the project from becoming "LLM prompt plus boxes."

## Sources Used

- EvoMass / optimization-based building massing typology exploration:
  typology-oriented design exploration, population search, performance implication feedback.
- Performance-based urban massing generation and optimization:
  massing plus layout variation, not only isolated object variation.
- Subtractive/additive architectural massing generation:
  form generation principles and topological variability.
- GitAgent:
  repo-native agent modularity through `agent.yaml`, `SOUL.md`, `RULES.md`, `memory/`, `skills/`, `hooks/`.
- OpenAI Agents SDK:
  named agents, tools, handoffs, guardrails, sessions, tracing.

## Method Layers

| Method Layer | Paper/Reference Idea | MAAS Implementation | Owning Agent |
|---|---|---|---|
| Constraint truth | Optimization/exploration must be bounded by objective checks. | FAR/BCR/height/legal-envelope metrics. | `law_graph_agent` |
| Parking-mass negotiation | Layout feasibility must affect massing, not be an afterthought. | parking count, mass-stage precheck, revision request. | `parking_agent` |
| Architectural language | Typology-oriented exploration needs explicit massing language. | primary/secondary language, composition rule, topology intent. | `llm_architect_agent` |
| Representation | Text must become inspectable design grammar. | MassDSL verb sequence and parameter-source contract. | `massdsl_agent` |
| Form generation | Additive/subtractive/hybrid/sectional principles generate topology. | source volumes, source surfaces, primitive roles, rule priors. | `maas_geometry_agent` |
| Legalized candidate | Generated mass must survive hard gates and repair accounting. | legal repair, `repair_delta`, `source_volume_repair_delta`. | `maas_geometry_agent` + `law_graph_agent` |
| Evaluation | Exploration needs quality/diversity/orderliness measures. | diversity, language-pair diversity, orderliness, fragment gates. | `grammar_critic_agent` |
| Evidence synthesis | Designers need insight into why options exist and fail. | final review, failure memory, remaining risks. | `review_agent` |
| Workflow | Multi-agent systems need handoffs and traceable state. | canonical handoff flow and AG-light/JSON_MODULES alignment. | `design_orchestrator` |

## Current Canonical Flow

```text
design_orchestrator
  -> law_graph_agent
  -> parking_agent
  -> llm_architect_agent
  -> massdsl_agent
  -> maas_geometry_agent
  -> grammar_critic_agent
  -> review_agent
```

## Required Folder Contract

Every domain agent folder must expose:

- `agent.py`: executable local contract.
- `card.py`: agent-card export.
- `agent.yaml`: identity, input/output contract, handoffs, responsibilities.
- `SOUL.md`: role identity and research responsibility.
- `RULES.md`: non-negotiable behavior constraints.
- `memory/MEMORY.md`: why this agent exists and what previous failures it prevents.

Compatibility exports such as `contract.py` remain allowed where the existing ARR endpoint imports them.

## Current Gap

The project now has modular agent folders, but the actual runtime is still closer to sequential evidence attachment than a full bidirectional negotiation loop.

Next research-grade implementation:

1. Add a shared `CandidateState` object.
2. Let `parking_agent` emit structured revision requests.
3. Let `llm_architect_agent` revise MassDSL language from those requests.
4. Let `maas_geometry_agent` recompile and re-run hard gates.
5. Store each loop as trace/failure memory.
