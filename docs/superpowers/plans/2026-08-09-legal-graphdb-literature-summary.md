# Legal Graph DB Literature Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a Korean Markdown literature review of three recent Legal/Regulatory Graph DB papers with a primary-paper selection and PPT-ready proposal copy.

**Architecture:** Use primary paper pages and full texts as the evidence layer, then synthesize a single review document organized into comparison, detailed summaries, 25_ACE mapping, research gap, and slide copy. Keep bibliographic facts, measured results, author claims, and our inferences visibly separate.

**Tech Stack:** Markdown, arXiv/DOI/official journal sources, local 25_ACE project documentation, `pdftotext`, `rg`.

## Global Constraints

- Compare exactly three 2026 papers.
- Select Montenegro et al. (2026) as the latest primary Legal Graph DB paper.
- Treat Xiao et al. (2026) as the closest full-system comparison to 25_ACE.
- Label preprint/poster, forthcoming issue dates, and evaluation limitations honestly.
- Do not claim that graph retrieval itself makes deterministic legal judgments.
- Do not claim live Neo4j verification in this document.
- Do not modify project code or unrelated user files.

---

### Task 1: Validate Full-Text Evidence

**Files:**
- Read: `docs/superpowers/specs/2026-08-09-legal-graphdb-literature-summary-design.md`
- Read: `ARR/backend/law/PIPELINE.md`
- Read: `ARR/backend/design/maas/agents/law_graph_agent/evidence.py`
- Read: `docs/ai-session-memory/proposal/README.md`

**Interfaces:**
- Consumes: official paper metadata and full-text method/result/limitation sections.
- Produces: a fact sheet for each paper containing bibliographic status, problem, method, graph representation, evaluation, result, and limitation.

- [ ] **Step 1: Read the full text of Montenegro et al.**

Confirm the two-stage SEMLEG-based ontology engineering and ontology-guided RDF extraction workflow, model names, reported alignment/predicate results, and the poster/demo status.

- [ ] **Step 2: Read the full text of Baldwin and Ghanavati.**

Confirm the three AI-policy sources, two ontology schemas, five evaluated LLMs, 42 QA tasks, six reasoning types, and the scope of the reported KG augmentation gains.

- [ ] **Step 3: Read the full text of Xiao et al.**

Confirm SGR-BIM's cross-modal regulatory/BIM graph, multi-hop spatial reasoning design, 679-query evaluation, 84.3% accuracy, 8.6-point improvement, and limitations.

- [ ] **Step 4: Cross-check local project claims.**

Verify that 25_ACE separates law retrieval/provenance from deterministic numerical and geometric validation and that the local law pipeline documents Neo4j hierarchy, embeddings, and search.

- [ ] **Step 5: Record citation dates accurately.**

Use 2026-07-27 for Montenegro et al., 2026-04-30 for Baldwin and Ghanavati, and note that Xiao et al. is online with DOI `10.1016/j.autcon.2026.107038` for the September 2026 issue.

### Task 2: Write the Proposal/PPT Literature Review

**Files:**
- Create: `collected_papers/legal/LATEST_LEGAL_GRAPHDB_PAPERS_2026.md`

**Interfaces:**
- Consumes: Task 1 fact sheets and the approved design.
- Produces: one self-contained Korean Markdown review ready for proposal and PPT use.

- [ ] **Step 1: Write the verdict and comparison table.**

State which paper is newest, which has the strongest evaluated compliance reasoning, and which is closest to 25_ACE's law-to-geometry workflow.

- [ ] **Step 2: Write one detailed section per paper.**

For each paper include `어떤 논문인가`, `문제`, `방법`, `데이터·평가`, `주요 결과`, `한계`, and `25_ACE와의 관계`.

- [ ] **Step 3: Write the integrated comparison with 25_ACE.**

Compare ontology/schema induction, legal hierarchy, graph storage, vector retrieval, temporal/version modeling, geometry reasoning, deterministic validation, provenance, and evaluation maturity.

- [ ] **Step 4: Write proposal-ready research-gap copy.**

Frame 25_ACE's contribution as integrating Korean statutory structure, PNU/site context, deterministic legal geometry, specialist-agent repair, and evidence lineage rather than inventing Legal KG or SGR-BIM independently.

- [ ] **Step 5: Write PPT-ready slide content.**

Provide a four-slide package with titles, three to five bullets per slide, one-line takeaway bars, and short speaker notes.

- [ ] **Step 6: Add references and direct primary links.**

Include arXiv links for the two preprints and the DOI/journal link for SGR-BIM. Add the 2025 SAT-Graph RAG paper only as dated background, not as one of the three compared papers.

### Task 3: Verify the Markdown Deliverable

**Files:**
- Verify: `collected_papers/legal/LATEST_LEGAL_GRAPHDB_PAPERS_2026.md`

**Interfaces:**
- Consumes: completed Markdown document.
- Produces: verified document with no placeholders, broken structure, or unsupported claims.

- [ ] **Step 1: Scan for placeholders and ambiguous publication claims.**

Run:

```powershell
rg -n "TBD|TODO|확인 필요|미정|출판 완료" collected_papers/legal/LATEST_LEGAL_GRAPHDB_PAPERS_2026.md
```

Expected: no output.

- [ ] **Step 2: Check required sections.**

Run:

```powershell
rg -n "^## (결론|최신 논문 3편 비교|논문 1|논문 2|논문 3|25_ACE와의 종합 비교|프로포절용 연구 공백|PPT 슬라이드 문안|참고문헌)" collected_papers/legal/LATEST_LEGAL_GRAPHDB_PAPERS_2026.md
```

Expected: all nine major sections are present.

- [ ] **Step 3: Check exact key facts.**

Run:

```powershell
rg -n "2607\.24551|2604\.27713|10\.1016/j\.autcon\.2026\.107038|679|84\.3|8\.6" collected_papers/legal/LATEST_LEGAL_GRAPHDB_PAPERS_2026.md
```

Expected: every identifier and reported SGR-BIM result appears in context.

- [ ] **Step 4: Check Markdown whitespace.**

Run:

```powershell
git diff --check -- collected_papers/legal/LATEST_LEGAL_GRAPHDB_PAPERS_2026.md
```

Expected: exit code 0 with no output.

- [ ] **Step 5: Commit only the literature review.**

```powershell
git add -- collected_papers/legal/LATEST_LEGAL_GRAPHDB_PAPERS_2026.md
git commit -m "docs: summarize latest legal graph literature" --only -- collected_papers/legal/LATEST_LEGAL_GRAPHDB_PAPERS_2026.md
```
