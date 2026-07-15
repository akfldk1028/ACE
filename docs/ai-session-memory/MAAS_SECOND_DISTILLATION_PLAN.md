# MAAS Second Distillation Plan

## Why This Exists

- User/professor feedback: after legal/parking/LLM MassDSL generation works,
  the system needs a second distillation stage for architectural preference.
- This is not the first target. First verify the generator against paper-method
  requirements in `MAAS_GENERATOR_PAPER_ALIGNMENT_AUDIT.md`.
- First-stage MAAS answers: "is this legal, parkable, and formally diverse?"
- Second-stage MAAS should answer: "which of the legal candidates would people,
  critics, or precedent-trained taste models prefer?"
- Do not solve this by asking one LLM to pick everything blindly. Use LLM/VLM as
  one critic in a measurable preference pipeline.

## Research Direction

- VLM is useful, but not sufficient by itself.
  - Do not ask a VLM to simply choose the "best" architecture.
  - Use it to extract structured concept evidence from PNGs.
  - Pairwise human/professor labels remain the stronger preference signal.
- Preference-learning papers suggest a pairwise preference route:
  - collect preferred vs rejected image pairs,
  - train or calibrate a reward/reranker,
  - apply the reranker after hard legal/parking filters.
- Personalized preference work shows a useful few-shot pattern:
  - a VLM can extract preference features from a small set of pairwise examples,
  - those features can condition a model or reward score for a specific user.
- Curriculum DPO suggests ordering pairs from easy to hard:
  - obvious wins first, close architectural choices later,
  - useful for professor/student critique sessions.
- Architectural AI papers support the split pipeline:
  - generate massing models parametrically,
  - evaluate or transform them with image/model-based methods,
  - keep performance/legal constraints separate from aesthetic generation.

## Proposed MAAS Pipeline

1. Generate many candidates.
   - LLM/agent proposes MassDSL language and parameters.
   - Deterministic compiler turns MassDSL into source geometry.
2. First distillation: hard feasibility.
   - legal envelope,
   - FAR/BCR/height,
   - parking formula/count/mass-stage,
   - source geometry and role-pattern diversity.
3. Render review artifacts.
   - PNG cards,
   - canonical isometric thumbnails,
   - optional larger hero renders for shortlisted candidates.
4. Second distillation: preference rerank.
   - VLM scores each PNG for architectural concepts:
     clarity, dominant gesture, silhouette, compositional hierarchy,
     publicness/void quality, non-stair dependence, precedent resonance.
   - Human or professor pairwise choices create `preferred > rejected` records.
   - A lightweight reranker calibrates VLM concept scores to local taste.
5. Return final set.
   - Keep law/parking pass mandatory.
   - Prefer high preference score only inside the legal candidate pool.
   - Keep a small number of exploratory outliers so the model does not collapse
     into one popular style.

## Data Sources

- Internal MAAS PNG outputs:
  - safest source,
  - has JSON labels and legal/parking metadata,
  - can generate many legal candidates cheaply once the LLM loop works.
- Crit session labels:
  - pairwise professor/student choices,
  - "A better than B because..." text,
  - converts naturally into Bradley-Terry / DPO-style data.
- Precedent/reference corpus:
  - user-provided books and reference boards,
  - public article metadata and tags where license allows,
  - ArchDaily-like sources can be used for metadata/research inspiration, but
    scraped images should not be blindly redistributed or embedded without
    checking rights.
- Public preference/image datasets:
  - useful for general aesthetic priors,
  - must be calibrated to architecture because generic image aesthetics can
    reward photorealism over massing quality.

## Implementation Shape

- Add `design/maas/preference/` module:
  - `concept_schema.py`: VLM concept score schema.
  - `vlm_scorer.py`: calls a VLM on candidate PNGs.
  - `pairwise_store.py`: stores human/preference comparisons.
  - `reranker.py`: combines VLM concepts, legal metrics, and learned weights.
- Add `design/maas/agents/preference_distiller_agent/` folder:
  - `agent.py`
  - `agent.yaml`
  - `SOUL.md`
  - `RULES.md`
  - `memory/MEMORY.md`
  - `card.py`
  - `contract.py`
- Add JSON evidence to each candidate:
  - `preference_distillation.schema_version = arr.maas.preference_distill.v1`
  - `concept_scores`
  - `vlm_model`
  - `precedent_tags`
  - `human_pairwise_wins`
  - `distilled_preference_score`
- Add a verifier:
  - every final top candidate still legal/parking pass,
  - no more than two stair/stepback-like masses unless explicitly selected as
    legal anchors,
  - second-stage score present for all review candidates,
  - final set includes both high-score choices and controlled diversity.

## Immediate Next Step

- Do not use second-stage preference to hide generator weakness.
- First add generator paper-alignment evidence/verifier:
  - typology generation,
  - source geometry lineage,
  - formal variation stage,
  - objective vector,
  - legal repair delta,
  - selection reason.
- Implement a non-training MVP:
  - produce PNG candidates,
  - ask VLM for structured concept scores,
  - use hand-authored weights plus professor pair labels,
  - rerank candidates after legal/parking pass.
- Later research extension:
  - train a small Bradley-Terry/logistic reranker on pairwise choices,
  - use curriculum pairs from easy to hard,
  - compare against pure LLM judge, pure geometry heuristic, and no second
    distillation.

## VLM Decision

VLM is a component, not the method.

Correct use:

- Input: canonical MAAS PNG plus candidate JSON evidence.
- Output: structured concept scores and short evidence fields.
- Concepts: gesture clarity, mass hierarchy, non-stair silhouette, void/public
  quality, precedent resonance, repair integrity.
- The VLM score is calibrated by professor/student pairwise labels.

Incorrect use:

- VLM as legal/parking authority.
- VLM as the only final selector.
- VLM judging polished render quality instead of massing quality.
- VLM hiding weak generator lineage or large legal repair.

Reference basis checked 2026-07-08:

- Personalized preference fine-tuning work supports extracting preference
  embeddings from small pairwise image examples with VLMs.
- VisionReward-style work supports fine-grained multi-dimensional visual
  preference scoring rather than one scalar beauty score.
- DesignPref-style visual design preference data shows professional visual
  preference can be subjective and inconsistent, so pairwise/local calibration
  is necessary.
- VLM/DPO work supports multimodal preference optimization, but that belongs
  after the hard-gated generator, not inside the legal solver.

## Local Source Code

- `clone/Personalized-Text-To-Image-Diffusion`
  - PPD official code.
  - Use only the VLM preference embedding/profile stage; the full diffusion
    fine-tuning stage is not open-sourced.
- `clone/VisionReward`
  - VisionReward official code.
  - Use its QA checklist + weighted score structure as the closest code pattern
    for MAAS architectural concept scoring.
- `docs/ai-session-memory/MAAS_VLM_PREFERENCE_SOURCE_AUDIT.md`
  - Tracks which papers have code, which do not, and what can be safely adapted.
