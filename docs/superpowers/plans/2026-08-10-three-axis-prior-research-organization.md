# Three-Axis Prior Research Organization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Organize the selected prior-research papers into `legal`, `mass`, and `mas` folders and produce an exactly three-slide Markdown storyline using one original paper figure per slide.

**Architecture:** Each research axis owns its selected PDF, detailed summary, and a `figures` directory. A root-level storyline references one figure and one paper from each axis without duplicating the source files.

**Tech Stack:** PowerShell file operations, Poppler `pdftotext`, PyMuPDF page rendering, PNG assets, Markdown.

## Global Constraints

- The final folder names are exactly `legal`, `mass`, and `mas`.
- Each research axis receives exactly one PPT slide.
- Every slide uses an original figure extracted from the selected paper PDF; no figure is redrawn.
- Existing unrelated workspace changes are preserved.
- PDF and PNG validation is required before completion.

---

### Task 1: Validate and normalize the three category folders

**Files:**
- Move: `collected_papers/maas/` to `collected_papers/mass/`
- Move: `collected_papers/multi_agent/` to `collected_papers/mas/`
- Preserve: `collected_papers/legal/`

**Interfaces:**
- Consumes: the existing `EvoMass_2024.pdf` and `Text2BIM_arXiv_2408.08054_v2.pdf` files plus the verified official MDPI PDF for Li et al. (2024).
- Produces: the stable category roots consumed by all later tasks.

- [ ] **Step 1: Verify the source and destination paths**

Run `Test-Path` for `collected_papers/maas`, `collected_papers/multi_agent`, and `collected_papers/legal`; verify that `collected_papers/mass` and `collected_papers/mas` do not already exist.

- [ ] **Step 2: Download and verify the selected Legal Graph DB paper**

Download the official MDPI PDF from `https://mdpi-res.com/d_attachment/information/information-15-00666/article_deploy/information-15-00666.pdf` to `collected_papers/legal/Legal_Knowledge_Graph_Neo4j_2024.pdf`. Read the first five bytes of all three selected PDFs and require `%PDF-`; run `pdftotext -f 1 -l 2` and require each selected-paper title.

- [ ] **Step 3: Move the category directories**

Use PowerShell `Move-Item -LiteralPath` with the exact verified paths. Do not move or rename `ARR/backend/design/maas` or any project-code directory.

- [ ] **Step 4: Verify the normalized paths**

Require these three paths:

```text
collected_papers/legal/Legal_Knowledge_Graph_Neo4j_2024.pdf
collected_papers/mass/EvoMass_2024.pdf
collected_papers/mas/Text2BIM_arXiv_2408.08054_v2.pdf
```

### Task 2: Place original paper figures inside their owning folders

**Files:**
- Move: `collected_papers/ppt_assets/legal_sgr_bim_fig1_framework.png` to `collected_papers/legal/figures/sgr_bim_fig1_framework.png`
- Move: `collected_papers/ppt_assets/legal_sgr_bim_fig2_cross_modal_graph.png` to `collected_papers/legal/figures/sgr_bim_fig2_cross_modal_graph.png`
- Move: `collected_papers/ppt_assets/legal_sgr_bim_fig4_kg_schema.png` to `collected_papers/legal/figures/sgr_bim_fig4_kg_schema.png`
- Move: `collected_papers/ppt_assets/mas_text2bim_fig1_workflow.png` to `collected_papers/mas/figures/text2bim_fig1_workflow.png`
- Create: `collected_papers/legal/figures/legal_kg_neo4j_fig1_framework.png`
- Create: `collected_papers/mass/figures/evomass_fig2_generation_procedure.png`

**Interfaces:**
- Consumes: the normalized category roots, page 4 of `Legal_Knowledge_Graph_Neo4j_2024.pdf`, and page 6 of `EvoMass_2024.pdf`.
- Produces: category-local relative image paths for the paper summaries and storyline.

- [ ] **Step 1: Create the category-local figure directories**

Create `legal/figures`, `mass/figures`, and `mas/figures` only after validating their parent paths are under `D:\Data\25_ACE\collected_papers`.

- [ ] **Step 2: Move the existing SGR-BIM and Text2BIM original figures**

Move the four existing PNG files with exact `Move-Item -LiteralPath` calls and require each destination file afterward.

- [ ] **Step 3: Extract the Legal Graph DB paper's original Fig. 1**

Use PyMuPDF at 4× scale to render page 4. Crop the complete legal knowledge acquisition and management framework, including the caption and the Neo4j knowledge-storage block, and save it as `legal/figures/legal_kg_neo4j_fig1_framework.png`.

- [ ] **Step 4: Render EvoMass PDF page 6 and crop original Fig. 2**

Use PyMuPDF at 4× scale to render page 6. Crop the paper's complete Fig. 2, including its caption, without changing the diagram content, and save it as `mass/figures/evomass_fig2_generation_procedure.png`.

- [ ] **Step 5: Inspect the extracted Legal and EvoMass figures**

Open both PNGs at original detail. Verify that Legal Fig. 1 contains the complete acquisition-to-Neo4j pipeline and that EvoMass Fig. 2 contains both subtractive and additive generation rows and its caption.

### Task 3: Update category summaries for one-slide use

**Files:**
- Create: `collected_papers/legal/SELECTED_PRIMARY_PAPER_LEGAL_KG_NEO4J_2024.md`
- Modify: `collected_papers/mass/SELECTED_PRIMARY_PAPER_EVOMASS_2024.md`
- Modify: `collected_papers/mas/SELECTED_PRIMARY_PAPER_TEXT2BIM_2026.md`

**Interfaces:**
- Consumes: the category-local figure paths from Task 2.
- Produces: one-slide content and 30-second script for each selected paper.

- [ ] **Step 1: Replace legacy figure paths**

Use category-local links `figures/legal_kg_neo4j_fig1_framework.png`, `figures/evomass_fig2_generation_procedure.png`, and `figures/text2bim_fig1_workflow.png` for the selected one-slide figures. Keep SGR-BIM figure links only in its secondary summary.

- [ ] **Step 2: Add or normalize the one-slide block in each summary**

Each block must contain a slide title, one original Figure, no more than four body bullets, a limitation/25_ACE connection, a source footnote, and a 30-second script.

- [ ] **Step 3: Validate Markdown links**

Resolve every local `.png` link relative to its Markdown file and require the target to exist.

### Task 4: Rewrite the integrated storyline as exactly three slides

**Files:**
- Modify: `collected_papers/PPT_PRIOR_RESEARCH_STORYLINE.md`
- Modify: `collected_papers/paper_index.md`

**Interfaces:**
- Consumes: the three selected-paper summaries and their category-local figure paths.
- Produces: the final three-slide prior-research sequence and an updated file index.

- [ ] **Step 1: Write Slide 1 — Legal Graph DB / Chinese Legal Knowledge Graph**

Emphasize heterogeneous legal sources, JKEM-based triple extraction, Neo4j as the core graph database, 3,480 triples, and 90.92% extraction accuracy. State that the criminal-law domain differs from building regulation but its graph construction and storage pattern is transferable.

- [ ] **Step 2: Write Slide 2 — Mass / EvoMass**

Emphasize subtractive/additive generation, typology-oriented exploration, island evolutionary optimization, and the lack of integrated domestic-code hard gates.

- [ ] **Step 3: Write Slide 3 — MAS / Text2BIM**

Emphasize the four specialist agents, IFC/Solibri/BCF feedback loop, final rule-pass results, and the absence of a persistent shared design-state Graph DB.

- [ ] **Step 4: Update the index paths**

Replace `maas/` with `mass/` for massing literature and `multi_agent/` with `mas/` for the selected MAS paper. Preserve the `legal/` paths.

### Task 5: Run final evidence-based verification

**Files:**
- Verify: all PDFs, PNGs, and Markdown files created or moved by Tasks 1–4.

**Interfaces:**
- Consumes: the complete organized artifact set.
- Produces: a pass/fail report that supports the completion claim.

- [ ] **Step 1: Verify PDFs**

Require `%PDF-`, extract first-page text, and report file size plus SHA-256 for all three selected PDFs.

- [ ] **Step 2: Verify PNGs**

Open each slide figure as PNG and report its dimensions. Require the Legal, Mass, and MAS one-slide figures to exist under their category folders.

- [ ] **Step 3: Verify Markdown requirements**

Require exactly three numbered slide headings in the integrated storyline, all three selected-paper names, all three category-local figure paths, balanced code fences, and no unfinished placeholder markers.

- [ ] **Step 4: Check legacy paths and workspace scope**

Search current collected-paper Markdown files for `collected_papers/maas`, `collected_papers/multi_agent`, `../ppt_assets`, and `ppt_assets/`. Report `git status --short` for only the affected artifact paths.
