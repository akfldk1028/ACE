# Prior Research PPT Assets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Download and summarize the SGR-BIM legal-compliance paper, extract only original paper figures for SGR-BIM and Text2BIM, and provide PPT-ready Korean storylines and speaking notes.

**Architecture:** Keep each selected paper in its existing topic folder with one canonical PDF and one detailed Markdown summary. Store cropped, unmodified paper figures in a shared `ppt_assets` folder and connect both studies in one storyline Markdown file.

**Tech Stack:** PowerShell, arXiv PDF, `pdftotext`, `pdftoppm`, ImageMagick when available, Markdown.

## Global Constraints

- Do not create or redraw diagrams.
- Use only figures contained in the source papers.
- Preserve figure content; only crop whitespace and render at readable resolution.
- Cite paper title, authors, year, figure number, and DOI alongside every PPT recommendation.
- Keep the existing French legal KG paper as a secondary reference.

---

### Task 1: Save and validate the SGR-BIM PDF

**Files:**
- Create: `collected_papers/legal/SGR_BIM_2026.pdf`

**Interfaces:**
- Consumes: arXiv PDF `https://arxiv.org/pdf/2606.12065`
- Produces: canonical local SGR-BIM PDF for text and figure extraction

- [ ] **Step 1: Download the PDF**

Run `Invoke-WebRequest` with the arXiv URL and save to the exact target path.

- [ ] **Step 2: Validate the file**

Check that the first five bytes equal `%PDF-`, file size exceeds 1 MB, and first-page text contains `Automating Geometry-Intensive Compliance Checking in BIM`.

- [ ] **Step 3: Record its SHA-256 hash**

Run `Get-FileHash -Algorithm SHA256` and retain the value for final verification.

### Task 2: Extract original SGR-BIM figures

**Files:**
- Create: `collected_papers/ppt_assets/legal_sgr_bim_fig1_framework.png`
- Create: `collected_papers/ppt_assets/legal_sgr_bim_fig2_cross_modal_graph.png`
- Create: `collected_papers/ppt_assets/legal_sgr_bim_fig4_kg_schema.png`

**Interfaces:**
- Consumes: `collected_papers/legal/SGR_BIM_2026.pdf`
- Produces: cropped source-paper figures for PPT insertion

- [ ] **Step 1: Locate figure pages**

Use form-feed-separated `pdftotext` output to identify the PDF page containing each exact caption: `Fig. 1`, `Fig. 2`, and `Fig. 4`.

- [ ] **Step 2: Render source pages**

Use `pdftoppm -png -r 220` for only the identified pages.

- [ ] **Step 3: Crop each figure**

Crop only surrounding page text and whitespace while retaining the complete figure and its caption. Do not alter labels, colors, arrows, or diagram contents.

- [ ] **Step 4: Inspect output**

Open all three PNGs and confirm the complete source figure and caption are legible.

### Task 3: Extract the original Text2BIM collaboration figure

**Files:**
- Create: `collected_papers/ppt_assets/mas_text2bim_fig1_workflow.png`

**Interfaces:**
- Consumes: `collected_papers/multi_agent/Text2BIM_arXiv_2408.08054_v2.pdf`
- Produces: original Text2BIM Fig. 1 for PPT insertion

- [ ] **Step 1: Locate and render Fig. 1**

Find the page whose caption is `Fig. 1. The proposed LLM-based multi-agent framework with a sample user instruction`, then render it at 220 DPI.

- [ ] **Step 2: Crop and inspect**

Retain the entire framework and caption, remove only surrounding body text and whitespace, and confirm all four agent roles and feedback arrows are legible.

### Task 4: Write the SGR-BIM summary and presentation material

**Files:**
- Create: `collected_papers/legal/SELECTED_PRIMARY_PAPER_SGR_BIM_2026.md`
- Modify: `collected_papers/paper_index.md`

**Interfaces:**
- Consumes: SGR-BIM PDF text and figures
- Produces: canonical legal Graph DB prior-research summary

- [ ] **Step 1: Write bibliographic and method sections**

Include formal citation, DOI, publication-year note, research problem, SGR-BIM architecture, cross-modal graph construction, multi-agent coordination, and figure explanations.

- [ ] **Step 2: Write results and limitations**

Verify and include 679 expert-verified fire-code queries, 84.3% accuracy, 8.6 percentage-point improvement, applicability boundary, and reproducibility/code status.

- [ ] **Step 3: Write proposal and PPT copy**

Include a full prior-research paragraph, a short paragraph, one-sentence slide copy, slide bullets, 30-second script, 60-second script, and 25_ACE comparison.

- [ ] **Step 4: Update the paper index**

Mark SGR-BIM as the selected legal Graph DB paper while retaining the French legal KG paper as secondary.

### Task 5: Add figure guidance to Text2BIM and connect the research storyline

**Files:**
- Modify: `collected_papers/multi_agent/SELECTED_PRIMARY_PAPER_TEXT2BIM_2026.md`
- Create: `collected_papers/PPT_PRIOR_RESEARCH_STORYLINE.md`

**Interfaces:**
- Consumes: both selected papers and extracted source figures
- Produces: a three-slide prior-research narrative

- [ ] **Step 1: Add original-figure instructions to Text2BIM**

Identify Fig. 1 as the recommended slide figure and explain what to point out during presentation without redrawing it.

- [ ] **Step 2: Write the integrated storyline**

Connect the studies as `SGR-BIM: law–BIM graph reasoning` plus `Text2BIM: specialized-agent generation and feedback`, followed by the shared research gap and 25_ACE contribution.

- [ ] **Step 3: Provide exact slide copy**

Supply slide titles, four or fewer bullets per slide, source footnotes, image filenames, and presentation scripts for the legal study, MAS study, and research-gap slide.

### Task 6: Verify all deliverables

**Files:**
- Verify: `collected_papers/legal/SGR_BIM_2026.pdf`
- Verify: `collected_papers/legal/SELECTED_PRIMARY_PAPER_SGR_BIM_2026.md`
- Verify: `collected_papers/multi_agent/SELECTED_PRIMARY_PAPER_TEXT2BIM_2026.md`
- Verify: `collected_papers/PPT_PRIOR_RESEARCH_STORYLINE.md`
- Verify: `collected_papers/ppt_assets/*.png`

**Interfaces:**
- Consumes: all task outputs
- Produces: evidence that every requested PDF, figure, and MD is usable

- [ ] **Step 1: Validate PDF and image files**

Confirm PDF signatures, PNG signatures, nonzero dimensions, and expected filenames.

- [ ] **Step 2: Validate MD requirements**

Check formal citations, figure references, PPT copy, scripts, project comparison, no `TODO` or `TBD`, and balanced code fences.

- [ ] **Step 3: Visually inspect all extracted figures**

Open every PNG and confirm it is an unmodified, readable source-paper figure with its caption.

- [ ] **Step 4: Review scoped changes**

Run `git status --short` for `collected_papers/legal`, `collected_papers/multi_agent`, `collected_papers/ppt_assets`, `collected_papers/PPT_PRIOR_RESEARCH_STORYLINE.md`, and `collected_papers/paper_index.md`.
