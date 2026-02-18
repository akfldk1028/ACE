# Multi-Agent Pattern Taxonomy (13 Patterns, 4 Categories)

## Overview

| ID | Category | Agents | Provider | Topology | Stop Keyword | MaxMsg | Expected Turns |
|----|----------|--------|----------|----------|-------------|--------|----------------|
| rr2 | A: Flat Sequential | 2 | RoundRobin | Ring-2 | TERMINATE | 10 | 4-6 |
| rr3 | A: Flat Sequential | 3 | RoundRobin | Ring-3 | TERMINATE | 10 | 6-9 |
| rr4 | A: Flat Sequential | 4 | RoundRobin | Ring-4 | TERMINATE | 12 | 8-12 |
| sel3 | B: Dynamic Routing | 3 | Selector | Star-3 | TERMINATE | 10 | 5-8 |
| sel4 | B: Dynamic Routing | 4 | Selector | Star-4 | TERMINATE | 12 | 6-10 |
| swm3 | B: Dynamic Routing | 3 | Swarm | Mesh-3 | TERMINATE | 10 | 4-7 |
| swm4 | B: Dynamic Routing | 4 | Swarm | Mesh-4 | TERMINATE | 12 | 5-9 |
| refl2 | C: Structured Feedback | 2 | RoundRobin | Loop-2 | APPROVED | 8 | 4-6 |
| refl3 | C: Structured Feedback | 3 | RoundRobin | Loop-3 | APPROVED | 10 | 6-9 |
| debate3 | C: Structured Feedback | 3 | Selector | Star-3 | VERDICT | 10 | 6-8 |
| debate4 | C: Structured Feedback | 4 | Selector | Star-4 | VERDICT | 12 | 7-10 |
| pipe | D: Composed/Nested | 3+2=5 | 2x team | Chain-2 | ANALYSIS_DONE->TERMINATE | 8+6 | 8-12 |
| moa | D: Composed/Nested | 3+1=4 | gather+1 | Fork-Join | MaxMsg | 3x3+2 | 4-8 |

## Category A: Flat Sequential

Sequential turn-taking. Fixed order. Measures agent-count effect on termination.

- **rr2**: Minimal unit. 2-agent ping-pong. Baseline for all comparisons.
- **rr3**: 3-agent pipeline. Does adding a reviewer help or hurt?
- **rr4**: Full 4-stage pipeline. Convergence speed of large rotations.

## Category B: Dynamic Routing

Agent selection varies at runtime. Measures routing strategy effect.

- **sel3**: LLM picks next speaker from 3 experts. Skips unnecessary agents?
- **sel4**: 4 experts. Does more choice → more turns or better quality?
- **swm3**: Handoff-based delegation. Self-routing via tool calls.
- **swm4**: Complex handoff mesh. Loop detection becomes important.

## Category C: Structured Feedback

Explicit feedback loops. Measures quality convergence vs overshoot.

- **refl2**: Generator-Critic loop. "Self-Refine" pattern.
- **refl3**: Generator-Critic-Editor. Does editor add value?
- **debate3**: Pro/Con/Judge. Clear convergence point (VERDICT).
- **debate4**: Pro/Con/Moderator/Judge. Moderator accelerates convergence?

## Category D: Composed/Nested

Multi-team compositions. Novel contribution - rarely studied.

- **pipe**: Pipeline (analysis team -> synthesis team). 2-stage termination.
- **moa**: Mixture of Agents (3 parallel -> 1 aggregator). Fork-join pattern.

## Research Questions Mapped to Patterns

| Research Question | Patterns | Comparison |
|-------------------|----------|------------|
| agent_count -> termination timing? | rr2/rr3/rr4 | Same topology, varying agents |
| Same agents, different topology? | rr3/sel3/swm3/refl2 | 3-agent, 4 topologies |
| Feedback loop vs one-way? | refl2 vs rr2, refl3 vs rr3 | Same agents, feedback toggle |
| Single team vs composed? | sel3 vs pipe(Stage1=sel3) | Pipeline wrapping effect |
| Moderator effect? | debate3 vs debate4 | Moderator addition |
| Dynamic vs fixed routing? | sel3 vs rr3 | Same 3-agent, routing varies |

## Academic Mapping

| Source | Key Insight | Our Coverage |
|--------|------------|-------------|
| Microsoft AI Agent Patterns | Sequential/Concurrent/GroupChat/Handoff/Magentic | A~D categories |
| Hierarchical MAS Taxonomy (2025) | CNP, FMH, Holarchy, 20+ patterns | D = Holarchy |
| MoA (ICLR 2025) | Multi-layer parallel, AlpacaEval 65.1% | moa pattern |
| Multi-Agent Collab Survey | Bus/Star/Ring/Tree/DAG topologies | All 5 covered |
