# Thesis Proposal PPT Outline

Target: 27-page academic proposal deck, following the reference proposal style in `docs/pp`.

## 1. Cover

Title:

> Graph DB와 협업형 멀티에이전트를 활용한 건축설계 자동화 및 법규 검증 방법 연구

Subtitle candidate:

> 대지·법규 지식 구조화와 에이전트 협업을 통한 초기 설계안 생성 및 검토 프로세스

## 2. Index

1. 서론
2. 선행 연구
3. 문제 제기
4. 연구 설계 방향
5. 결론

## 3. Section Divider: Introduction

Theme:

> 건축 초기 설계는 형태 생성이 아니라 조건 충족과 의사결정의 반복 과정이다.

Visual:

- Site, law, parking, mass, agent, graph icons or diagram.

## 4. Background: Early Design Complexity

Message:

Early design must combine site conditions, zoning, program, BCR/FAR, parking, daylight, road constraints, and design intent.

Visual:

- One site parcel in the center.
- Around it: 법규, 대지, 주차, 일조, 용적률, 형태, 검증.

## 5. Legal Complexity

Message:

건축 법규는 단일 조항이 아니라 법, 시행령, 시행규칙, 주차장법, 조례, 용도지역, 대지 조건이 결합된 복합 체계다.

Must include:

- 건축법
- 건축법 시행령
- 시행규칙
- 주차장법
- 지자체 조례
- 용도지역
- 도로/일조/사선
- 건폐율/용적률

## 6. Practical Problem: Iterative Rework

Message:

Design generation and legal review are separated, causing repeated cycles:

```text
설계안 작성 -> 법규 검토 -> 위반 발견 -> 수정 -> 재검토
```

Parking example:

- Required parking count can pass legally.
- Actual parking layout can still fail geometrically.

## 7. Why Existing AI Is Not Enough

Message:

Generative AI can produce plausible forms, but legal validity and evidence are not guaranteed.

Contrast:

- AI image/3D generation: strong visual output.
- Legal design verification: needs traceable basis and deterministic checks.

## 8. Why Multi-Agent

Message:

Law search, parking review, geometry repair, design generation, and final review are different expert tasks.

Agent roles:

- Law Agent
- Parking Agent
- Design/MAAS Agent
- Geometry Agent
- Review Agent

## 9. Why Graph DB

Message:

The system needs to store relationships among laws, parcels, candidates, violations, repairs, evidence, and final decisions.

Visual:

```text
Parcel -> Law Article -> Constraint -> Candidate -> Violation -> Repair -> Evidence -> Decision
```

## 10. Research Question

Main question:

> Graph DB 기반 법규 지식과 협업형 멀티에이전트를 활용하여, 초기 건축설계안을 생성하고 법규 검증 근거까지 추적할 수 있는가?

Sub-questions:

- How can legal rules and site conditions be structured for design generation?
- How can generated candidates be validated and repaired?
- How can agents collaborate while preserving evidence and decision lineage?

## 11. Section Divider: Related Work

Theme:

> 최신 연구는 생성, 최적화, 법규 검토, 제약조건 처리로 발전 중이지만 통합 루프는 아직 부족하다.

## 12. Related Work 1: Optimization-Based Massing

Primary references:

- Lou et al. 2025, Scientific Reports.
- Wang et al. 2024, Frontiers of Architectural Research.
- Wang 2022, EvoMass workflow.
- Wang, Janssen, Ji 2020, SSIEA original algorithm.

Message:

Massing optimization can produce multiple alternatives, but legal evidence and Korean regulation integration remain outside the main scope.

## 13. Related Work 2: Constraint-Aware Generation

Primary references:

- PGDM, NeurIPS 2024.
- CDD, NeurIPS 2025.
- Training-free constrained generation, NeurIPS Spotlight 2025.
- PPR, 2026.
- Boundary-constrained floorplan diffusion, 2026.

Message:

Recent AI generation research tries to enforce constraints, but architectural law requires domain-specific validators and repair logic.

## 14. Related Work 3: Architectural 3D and Diffusion

Primary references:

- Tsai and Hariharan 2025, WACV.
- Zhang et al. 2024, diffusion-based 3D architectural form-finding.
- UniTEX, CVPR 2026 / arXiv 2025.
- Make-A-Texture 2025, MVPainter, TexFusion.

Message:

Visual generation is advancing, but it does not replace legal mass generation and verification.

## 15. Related Work 4: Code Compliance and Legal AI

References:

- LLM-FuncMapper 2023.
- LLM-assisted building design alterations / code compliance 2025.
- BuildThemis 2025-style RAG/code compliance direction.

Message:

Code compliance research supports legal interpretation and checking, but generation, parking feasibility, geometry repair, and evidence lineage must be connected.

## 16. Related Work Synthesis

Table columns:

- Research area
- Strength
- Limitation
- Position of this research

Rows:

- Massing optimization
- Constraint-aware AI generation
- Architectural 3D/diffusion
- Code compliance
- Multi-agent systems
- Graph DB/legal evidence

Core statement:

> Existing studies solve parts of the workflow, but not the full loop of legal knowledge, candidate generation, deterministic validation, agent repair, and evidence tracking.

## 17. Section Divider: Problem Definition

Theme:

> The target problem is verifiable design automation, not form generation alone.

## 18. Problem 1: Legal Rules Are Fragmented

Message:

Regulatory information is scattered across laws, decrees, rules, ordinances, and site-specific conditions.

Need:

Graph-based legal/site knowledge structure.

## 19. Problem 2: Legal Conditions Become Geometry

Message:

BCR/FAR, setbacks, daylight, road constraints, height limits, and parking are not only text rules. They become geometry and layout constraints.

Need:

Deterministic legal/geometry validators.

## 20. Problem 3: Generation and Review Are Disconnected

Message:

Current workflows often generate first and check later. This causes repeated manual repair and weak traceability.

Need:

Closed-loop generation, validation, repair, and review.

## 21. Section Divider: Proposed Method

Theme:

> Graph DB + deterministic validators + collaborative agents.

## 22. Proposed System Overview

Diagram:

```text
PNU/Site Input
-> Legal Graph DB
-> MAAS Candidate Generator
-> Legal/Parking/Geometry Validators
-> Multi-Agent Review
-> Repair or Select
-> Evidence and Lineage Graph
```

## 23. Agent Collaboration Workflow

Agent chain:

```text
law_graph_agent
-> parking_agent
-> maas_geometry_agent
-> design_optimizer_agent
-> review_agent
```

Message:

Agents do not replace validators. They coordinate evidence, request repair, and explain decisions.

## 24. Graph DB Evidence Model

Store:

- Parcel
- Legal article
- Regulation constraint
- Candidate
- Generated geometry
- Validation result
- Violation
- Requested repair
- Agent review
- Evidence artifact
- Final decision
- Candidate lineage

## 25. Implementation and Current Verification

Current evidence:

- successful_scenarios = 4/4
- feature_count = 80
- 20 unique-shape candidates per scenario target
- section_connector_feature_count = 11
- legal_pass_rate = 1.0

Tests:

- py_compile
- MAAS sequence metric
- diversity selection
- benchmark JSON target tests

Implementation references:

- MAAS benchmark and section-profile verification.
- Parking legal graph and layout checks.
- AG-light multi-agent team.
- Neo4j law/provenance graph.

## 26. Expected Contribution

Contribution:

- A graph-based structure for connecting architectural law, site data, candidates, evidence, and decisions.
- A multi-agent workflow for law review, parking review, geometry repair, and design review.
- A deterministic generation and validation loop for early-stage architectural design alternatives.
- A traceable evidence model for why a candidate passed, failed, or was repaired.

## 27. Conclusion and Q&A

Closing sentence:

> 본 연구는 건축설계 자동화의 목표를 단순한 형상 생성이 아니라, 법규 근거와 검증 이력이 추적 가능한 설계안 생성 과정으로 확장한다.

