# NotebookLM and Slide-Generation Prompts

Use these prompts after uploading the proposal memory files and project references to NotebookLM.

## Recommended Sources to Upload

Upload these first:

- `docs/ai-session-memory/proposal/README.md`
- `docs/ai-session-memory/proposal/PROBLEM_CONTEXT.md`
- `docs/ai-session-memory/proposal/LATEST_LITERATURE.md`
- `docs/ai-session-memory/proposal/PPT_OUTLINE.md`
- `docs/ai-session-memory/MAAS_RESEARCH.md`
- `docs/ai-session-memory/MULTI_AGENT_LEGAL_DESIGN_WORKFLOW.md`
- `docs/260506/research/02_RELATED_PAPERS.md`
- `docs/260506/research/03_RECOMMENDED_CITATIONS.md`
- `docs/260506/research/05_OUR_POSITION.md`

If possible, also upload screenshots or exported images from `docs/pp` as a style reference.

## Prompt 1: Source-Grounded Proposal Deck

```text
Create a Korean academic thesis proposal slide deck based strictly on the uploaded sources.

Audience:
- Architecture professors and design researchers.
- Some reviewers may not be engineering or AI specialists, so the narrative must be understandable without assuming deep knowledge of algorithms, Graph DB, or multi-agent systems.

Deck goal:
Explain the research problem, why it matters in architectural design, what gap exists in prior work, and how the proposed Graph DB + collaborative multi-agent workflow solves it.

Working title:
"Graph DB와 협업형 멀티에이전트를 활용한 건축설계 자동화 및 법규 검증 방법 연구"

Core argument:
Architectural design automation should not be framed as simple mass generation. The real problem is generating and reviewing early-stage design alternatives while preserving legal basis, validation evidence, violations, repair requests, and candidate lineage.

Required narrative:
1. Start from the practical difficulty of early architectural design.
2. Explain that Korean building regulations are fragmented across acts, enforcement decrees, enforcement rules, parking law, local ordinances, zoning, road constraints, daylight rules, BCR/FAR, and site-specific geometry.
3. Use parking as an intuitive example: calculating required parking count is a legal problem, while placing parking spaces is a geometric feasibility problem.
4. Explain why a single generative AI model is insufficient: it can generate plausible forms but cannot guarantee legal validity or traceable evidence.
5. Explain why a single rule-checking system is also insufficient: it can check rules but is often disconnected from design generation and repair.
6. Introduce Graph DB as the structure for connecting laws, site data, design candidates, constraints, violations, evidence, repair requests, and decisions.
7. Introduce multi-agent collaboration as role-based work division: Law Agent, Parking Agent, Design/MAAS Agent, Geometry Agent, Review Agent.
8. Emphasize that deterministic validators remain the source of legal and geometric truth; agents coordinate, critique, request repair, and explain evidence.
9. Present the latest literature from 2024-2026 first, including optimization-based massing, constraint-aware generation, architectural 3D/diffusion, and code compliance/legal AI.
10. State the research gap: existing studies solve parts of the workflow, but do not integrate legal Graph DB, design generation, deterministic validation, multi-agent repair, and evidence lineage into one architectural design workflow.

Deck structure:
- 27 slides.
- Use the uploaded PPT outline as the primary page order.
- Use Korean slide text.
- Use concise academic language.
- One main idea per slide.
- Prefer diagrams, process flows, comparison tables, and evidence maps over dense paragraphs.
- Include slide titles and speaker notes for each slide.

Visual style:
- Academic proposal style.
- Use a white or near-white background. This is mandatory.
- Use architectural diagram aesthetics: thin light-gray construction lines, subtle grids, site-plan-like linework, clean node-link diagrams, and calm spatial layouts.
- Use deep green or dark teal only as an accent, not as a full background.
- Use light gray lines for diagrams, connectors, graph edges, table rules, and section dividers.
- Use restrained colors: white, warm light gray, deep green/dark teal, charcoal text, and muted rust only for violations or repair warnings.
- Similar to the uploaded reference proposal images if available, but cleaner and more architectural.
- Use diagrams for Graph DB, multi-agent workflow, legal hierarchy, parking law example, and generate-verify-repair loop.
- Avoid dark backgrounds, decorative gradients, neon colors, playful icons, cartoon visuals, glossy startup pitch styling, and generic AI robot imagery.
- The deck must look like a serious graduate architecture-school thesis proposal.

Important constraints:
- Do not claim that this research invented SSIEA, EvoMass, diffusion, or general multi-agent systems.
- Say that this research integrates recent optimization/generation/code-compliance directions into a Korean architectural regulation and evidence-tracking workflow.
- Do not overfocus on "mass generation"; use "architectural design automation and regulatory verification."
- If a detail is not supported by the sources, mark it as "needs verification" instead of inventing it.
```

## Prompt 2: Ask NotebookLM to Improve the Story Before Slides

Use this before generating the slide deck if the first output feels too technical.

```text
Before making slides, rewrite the proposal narrative as a clear problem-solution story for architecture professors.

Use only the uploaded sources.

The story must answer:
1. What is difficult in early architectural design?
2. Why are building regulations, enforcement decrees, enforcement rules, parking law, local ordinances, BCR/FAR, daylight, road constraints, and geometry hard to handle together?
3. Why is parking a useful example of the gap between legal calculation and geometric feasibility?
4. Why is single-agent AI insufficient?
5. Why does Graph DB help?
6. Why does a collaborative multi-agent workflow help?
7. What is the research gap in recent 2024-2026 literature?
8. What is the proposed method?
9. What should the thesis contribution claim, and what should it avoid claiming?

Output:
- A 10-paragraph Korean narrative.
- A 5-bullet research gap.
- A 5-bullet contribution list.
- A one-sentence thesis claim.
```

## Prompt 3: Presenter Slides, Not Reading Slides

```text
Create a Presenter Slides version of the thesis proposal deck.

Use only the uploaded sources.

Requirements:
- 27 slides.
- Korean text.
- Each slide should have a short title, 3-5 concise bullets, and speaker notes.
- The deck must be understandable to non-engineering architecture professors.
- Avoid algorithm-heavy explanations on the main slides; put technical details in speaker notes.
- The central storyline must be:
  legal complexity -> disconnected generation/review -> need for evidence -> Graph DB -> multi-agent collaboration -> deterministic verification -> proposed workflow.
- Include latest research from 2024-2026, but make the literature section support the problem, not dominate the presentation.
```

## Prompt 4: Detailed Deck for Reading

```text
Create a Detailed Deck version of the thesis proposal that can be read without a presenter.

Use only the uploaded sources.

Requirements:
- 27 slides.
- Korean text.
- Each slide should include enough explanation to stand alone.
- Include citations or source references where NotebookLM can provide them.
- Use diagrams and tables where possible.
- Explain technical terms briefly when first introduced: Graph DB, deterministic validator, multi-agent workflow, candidate lineage, evidence artifact.
```

## Prompt 5: Antigravity / Gemini / Other Coding Agent PPT Build Prompt

Use this if exporting the NotebookLM outline to another agent to make a PPTX or HTML deck.

```text
You are creating an academic thesis proposal deck from the attached NotebookLM outline and source notes.

Build a 27-slide Korean presentation.

Topic:
Graph DB와 협업형 멀티에이전트를 활용한 건축설계 자동화 및 법규 검증 방법 연구

Audience:
Architecture professors, including reviewers who are not engineering or AI specialists.

Narrative:
1. Early architectural design is a complex decision process, not just form generation.
2. Korean building regulation is fragmented across laws, enforcement decrees, enforcement rules, parking law, ordinances, zoning, road/daylight constraints, BCR/FAR, and site geometry.
3. Parking demonstrates the core difficulty: legal required count and geometric placement feasibility must both be checked.
4. Existing generative design can produce alternatives, but legal evidence is weak.
5. Existing code compliance can check rules, but it is often disconnected from generation and repair.
6. The proposed method integrates Graph DB, deterministic validators, MAAS candidate generation, and role-based multi-agent collaboration.
7. Agents do not invent legal geometry. They coordinate law review, parking review, geometry repair, design regeneration, and final evidence summary.

Design style:
- Academic proposal deck.
- White background.
- Dark teal or green accent.
- Clean diagrams and tables.
- One idea per slide.
- Avoid decorative gradients and marketing-style hero slides.

Required slides:
Use the 27-page outline from the source notes. Include:
- cover
- index
- legal complexity
- parking example
- why single AI is insufficient
- why Graph DB
- why multi-agent
- latest 2024-2026 literature
- research gap
- proposed method
- agent workflow
- Graph DB evidence model
- current implementation and verification
- expected contribution
- conclusion

Technical constraints:
- Do not claim the research invented SSIEA, EvoMass, diffusion models, or multi-agent systems.
- Position the contribution as system integration for Korean architectural law, deterministic verification, evidence tracking, and collaborative agent workflow.
- Keep main-slide text concise; use speaker notes for details.
```

## Prompt 6: Visual Theme Only

Use this when NotebookLM asks only for a deck theme or style instruction.

```text
Use a refined graduate architecture thesis proposal visual theme.

Mandatory background:
- White or near-white background on all slides.
- No dark full-slide backgrounds.
- No colorful gradient backgrounds.

Diagram language:
- Architectural diagram style.
- Thin light-gray construction lines.
- Subtle grid references.
- Clean legal flowcharts.
- Graph DB node-link diagrams with light-gray edges.
- Multi-agent workflow diagrams with restrained green accents.
- Site-plan and massing-diagram visual language.

Color palette:
- Background: #FFFFFF or #F7F8F5.
- Main text: #1F2933.
- Light diagram/grid lines: #D8DDD6.
- Primary accent: #0F4C3A.
- Secondary accent: #2F6F5E.
- Warning/violation only: #B85C38.

Typography and layout:
- Clean academic sans-serif typography.
- Large but restrained slide titles.
- Generous margins.
- One main idea per slide.
- Avoid dense paragraphs.
- Use tables, process diagrams, evidence maps, and comparison matrices.

Avoid:
- Startup pitch style.
- Marketing hero slides.
- Neon colors.
- Cartoon icons.
- Glossy 3D tech graphics.
- Generic robot/AI illustrations.
- Overly decorative slides.

The final deck should look elegant, rigorous, and architectural, with white space and light-gray diagram lines as the dominant visual impression.
```
