# Latest Legal Graph DB Literature Summary Design

Date: 2026-08-09

## Purpose

Create one proposal-ready Markdown review focused only on recent legal and
regulatory knowledge-graph research. The review will compare three recent
papers, select one primary paper, and map their methods to the existing Korean
law Neo4j and MASS legal-evidence workflow in 25_ACE.

## Output

The final review will be written to:

`collected_papers/legal/LATEST_LEGAL_GRAPHDB_PAPERS_2026.md`

It will be a concise Korean-language literature note suitable for reuse in a
research proposal. It will not modify code, download PDFs, or claim that the
local Neo4j services were live-verified.

## Paper Set

1. **Primary/latest paper**: Montenegro et al. (2026), *LLM-Assisted Ontology
   Engineering and Construction of a French Legal Knowledge Graph*, arXiv
   2607.24551 / SEMANTiCS 2026 poster and demo proceedings.
2. **Compliance-reasoning comparison**: Baldwin and Ghanavati (2026),
   *Knowledge Graph Representations for LLM-Based Policy Compliance
   Reasoning*, arXiv 2604.27713.
3. **Project-fit comparison**: Xiao et al. (2026), *Automating
   Geometry-Intensive Compliance Checking in BIM: Graph-Based Semantic
   Reasoning Framework*, *Automation in Construction*, 189, 107038.

An additional note will correct a discovery-date ambiguity: *An
Ontology-Driven Graph RAG for Legal Norms* was first published online on
2025-12-04, so it is useful background for hierarchy, temporal versioning, and
provenance, but it is not one of the three 2026 comparison papers.

## Selection Logic

The French Legal Knowledge Graph paper will be selected as the primary paper
because it is the newest verified paper and directly studies the construction
of an ontology-grounded legal graph from regulatory text. Its two-stage design
also maps cleanly to the local project:

1. ontology/schema engineering;
2. schema-guided entity and relation extraction;
3. graph construction;
4. downstream retrieval and operational use.

SGR-BIM will be identified as the paper closest to the complete 25_ACE product
vision because it connects regulatory semantics to geometry-intensive
compliance checking. It is not selected as the primary Legal Graph DB paper
because its main contribution is BIM spatial reasoning rather than legal graph
construction itself.

## Final Document Structure

1. Short verdict and primary-paper selection.
2. Comparison table covering date, domain, graph construction, reasoning,
   evaluation, strength, and limitation.
3. Detailed summary of each paper.
4. Direct comparison with 25_ACE:
   - Korean law hierarchy and Neo4j ingestion;
   - vector and graph retrieval;
   - deterministic FAR/BCR/height/geometry validation;
   - law-source provenance bound to candidate identity;
   - current gaps in ontology induction, amendment/version modeling, and
     end-to-end evaluation.
5. Proposal-ready research-gap paragraph.
6. Recommended citation sentences.
7. References with DOI or primary paper links.

## Accuracy Rules

- Distinguish publication dates from search-index dates.
- Label arXiv or poster/demo work honestly; do not present it as a mature
  journal study.
- Do not equate graph retrieval with deterministic legal judgment.
- Do not claim the local system automatically translates all Korean clauses
  into executable constraints.
- State that SGR-BIM's September 2026 issue date is forthcoming relative to the
  current date, while its paper and DOI are already available online.
- Use paraphrases rather than long quotations.

## Success Criteria

- Exactly three 2026 papers are compared.
- One primary paper is selected with an explicit reason.
- The comparison distinguishes graph construction, retrieval, and compliance
  execution.
- The project comparison contains both strengths and honest implementation
  gaps.
- The final Korean text can be pasted into the proposal without rewriting its
  core claims.
