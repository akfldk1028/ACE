# Proposal Memory

This folder stores the working memory for the thesis proposal deck.

## Active 2026-08-06 Page Copy

- Working slide images: `docs/proposal/260806/`
- Page-by-page copy and speaker notes:
  `docs/proposal/260806/260806_페이지별_원고.md`
- Copy decisions and continuation handoff:
  `260806_PAGE_COPY_MEMORY.md`

The current editing rule is to preserve the user's existing slide layout and
write only the text that belongs in each visible placeholder, lower blue bar,
or speaker-note section. Read the actual slide image before revising a page.

## Working Title

Korean:

> Graph DB와 협업형 멀티에이전트를 활용한 건축설계 자동화 및 법규 검증 방법 연구

English:

> A Study on Architectural Design Automation and Regulatory Verification Using Graph DB and Collaborative Multi-Agent Systems

## Core Framing

The proposal should not be framed as simple mass generation. The research problem is broader:

- Early architectural design must handle site data, zoning, building regulations, parking, FAR/BCR, setbacks, daylight, road constraints, geometry, and design intent together.
- Korean building regulation is not a single rule. It spans acts, enforcement decrees, enforcement rules, parking law, local ordinances, zoning conditions, and case-specific geometry.
- Generative AI can produce shapes, but it cannot reliably prove legal validity or preserve evidence.
- Rule-checking systems can inspect designs, but they are often separated from design generation and iterative repair.
- A single AI agent is a poor fit because law search, parking calculation, geometry repair, design generation, and final review are different tasks.

## Proposed Answer

Use a Graph DB and collaborative multi-agent workflow around deterministic design and verification tools.

System concept:

```text
Site/PNU input
-> Legal and parcel Graph DB
-> MAAS candidate generation
-> deterministic legal/parking/geometry validators
-> agent collaboration and repair requests
-> regenerated candidates
-> evidence, decision, and lineage storage
```

## Required Proposal Message

The main claim should be:

> The goal of architectural design automation is not just generating forms, but generating verifiable design alternatives whose legal basis, violations, repair decisions, and final review evidence can be traced.

## Must-Include Components

- Korean legal complexity: acts, enforcement decrees, enforcement rules, parking law, local ordinance, zoning, road, daylight, FAR/BCR.
- Parking as an intuitive example: required parking count and actual geometric placement are different problems.
- Graph DB: connects law articles, site conditions, design objects, constraints, violations, evidence, repair requests, and candidate lineage.
- Multi-agent workflow:
  - Law Agent
  - Parking Agent
  - Design/MAAS Agent
  - Geometry Agent
  - Review Agent
- Deterministic validators must remain the source of geometric/legal truth.
- Agents should coordinate, critique, request repair, explain, and summarize evidence.

## Current Implementation References

- MAAS candidate generation and benchmark verification.
- Section profile verification.
- Parking graph/count/layout checks.
- Neo4j law/provenance graph.
- AG-light / A2A / AutoGen-style team workflow.
- `law_graph_agent`, `parking_agent`, `maas_geometry_agent`, `review_agent`.
