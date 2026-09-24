# Latest Literature Positioning

The proposal should foreground recent work from 2024-2026. Older procedural and graph grammar studies can be cited as background, but the slides should lead with current research.

## 1. Optimization-Based Massing

Primary recent references:

- Lou et al. 2025, Scientific Reports, "Multi-objective optimization of daylighting performance and solar radiation for building geometry using a hybrid evolutionary algorithm."
- Wang et al. 2024, Frontiers of Architectural Research, optimization-based design exploration of building massing typologies using EvoMass.
- Wang 2022, International Journal of Architectural Computing, EvoMass workflow for early-stage architectural design.

Background reference:

- Wang, Janssen, Ji 2020, AI EDAM, SSIEA original algorithm.

Proposal position:

> These studies show that optimization-based massing can generate and compare alternatives. This research does not claim to invent SSIEA/EvoMass; it integrates similar optimization logic with Korean legal Graph DB, deterministic verification, multi-agent review, and evidence tracking.

## 2. Constraint-Aware Generative Models

Primary recent references:

- Christopher et al. 2024, NeurIPS, Projected Diffusion Models.
- Cardei et al. 2025, NeurIPS, Constrained Discrete Diffusion.
- Zampini et al. 2025, NeurIPS Spotlight, training-free constrained generation.
- Rochman-Sharabi and Louppe 2026, Predict-Project-Renoise.
- Stoppani et al. 2026, boundary-constrained floorplan diffusion.

Proposal position:

> Recent AI research is moving toward constrained generation, but Korean architectural law introduces nontrivial geometric and legal constraints that still require deterministic validators and domain-specific repair loops.

## 3. Architectural 3D and Diffusion

Primary recent references:

- Tsai and Hariharan 2025, WACV, "3D Synthesis for Architectural Design."
- Zhang et al. 2024, Frontiers of Architectural Research, diffusion-based 3D architectural form-finding.
- LoRA-based architectural massing 2025.
- UniTEX, CVPR 2026 / arXiv 2025.
- Make-A-Texture 2025, MVPainter, TexFusion.

Proposal position:

> Architectural 3D generation and facade/texturing research is advancing quickly, but visual synthesis alone does not solve legal validity. In this project, visual/aesthetic synthesis is downstream of legal mass and geometry verification.

## 4. Code Compliance and Legal AI

Relevant references from project memory:

- Zhang et al. 2023, LLM-FuncMapper: translating regulatory clauses into executable functions.
- Wu et al. 2025, LLM-assisted building design alterations / code compliance.
- BuildThemis 2025-style RAG and code compliance direction.

Proposal position:

> Code compliance research helps translate or check regulations, but the remaining gap is a closed loop between legal evidence, design generation, geometry repair, parking feasibility, and candidate lineage.

## 5. Multi-Agent and Graph DB Position

This part should combine external research direction with local implementation evidence:

- AG-light / A2A / AutoGen-style collaboration.
- Neo4j legal/provenance graph.
- `law_graph_agent`, `parking_agent`, `maas_geometry_agent`, `review_agent`.
- Agent outputs should become graph evidence, not just chat logs.

Proposal position:

> Multi-agent collaboration is useful only when agents are grounded in deterministic tools and durable evidence. This research uses agents to coordinate law search, parking review, mass generation, repair requests, and final review while Graph DB stores the trace.

## Slide-Level Literature Flow

Recommended proposal slides:

1. Recent optimization-based massing: Lou 2025, Wang 2024, EvoMass/SSIEA.
2. Constraint-aware generation: PGDM 2024, CDD 2025, PPR 2026.
3. Architectural 3D/diffusion: Tsai 2025, Zhang 2024, UniTEX 2026.
4. Code compliance/legal AI: LLM-FuncMapper, BuildThemis, LLM-assisted compliance.
5. Gap synthesis: generation, verification, evidence, graph memory, and multi-agent repair are not yet integrated as one architectural design workflow.

