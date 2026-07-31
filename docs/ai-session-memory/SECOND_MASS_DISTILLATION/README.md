# Second Mass Distillation Memory

Updated: 2026-07-08

This folder is the working memory for MAAS second-stage mass preference
distillation. It mirrors the agent-folder principle: method, code sources,
datasets, harness, and failure conditions live together instead of being spread
across ad hoc notes.

## Current Method

```text
MAAS legal candidates
-> legal/parking/paper-alignment hard gates
-> canonical PNG evidence
-> Hugging Face / ArchDaily reference corpus
-> OpenAI VLM architecture QA scoring
-> professor/user pairwise labels
-> constrained reranker
-> final preference-ranked legal candidates
```

## 2026-07-08 Implementation Status

- Implemented the paper/code split:
  - `paper_sources.py` records paper URLs, official code URLs, local clone paths,
    and MAAS adaptation limits.
  - VisionReward maps to architecture-specific QA + weighted concept scoring.
  - PPD maps to pairwise preference/profile storage and win-rate style
    evaluation.
- Implemented the harness:
  - reads latest MAAS JSON,
  - backfills paper-alignment evidence when needed,
  - attaches `preference_distillation`,
  - matches external references,
  - applies pairwise wins,
  - reranks only hard-gated candidates.
- Smoke output:
  - `docs/playwright/design-route-live-verify/maas-20-alt-preference-latest.json`
  - `docs/playwright/design-route-live-verify/maas-20-alt-preference-latest.png`
  - MAAS JSON verifier: pass.
  - MAAS PNG verifier: pass.
  - parking verifier: pass.
  - VLM mode in the smoke run: `vlm_ready_geometry_proxy`.
  - Preference quality audit: pass.
- Real VLM output:
  - `docs/playwright/design-route-live-verify/maas-20-alt-vlm-latest.json`
  - `docs/playwright/design-route-live-verify/maas-20-alt-vlm-latest.png`
  - candidate crops:
    `docs/playwright/design-route-live-verify/preference-crops/latest/`
  - VLM mode: `vlm_scored` for 20/20 candidates.
  - VLM model used: `gpt-4.1-mini`.
  - Preference quality audit: pass.
  - MAAS JSON verifier: pass.
  - MAAS PNG verifier: pass.
  - parking verifier: pass for mass-stage count/formula only.
- ArchDaily external reference crawl:
  - Playwright browser probe currently times out on
    `https://www.archdaily.com/search/projects`.
  - Static HTML returns HTTP 200 but does not server-render project cards.
  - The ArchDaily search app JSON API works:
    `/search/api/v1/us/projects`.
  - Current structured DB: 119 unique ArchDaily references loaded by harness,
    175 downloaded images across API and seeded collections.

## Source Papers And Code

- PPD / CVPR 2025:
  - local code: `clone/Personalized-Text-To-Image-Diffusion`
  - use: few-shot pairwise preference examples and user preference profile.
  - caution: only VLM Stage 1 is public.
- VisionReward:
  - local code: `clone/VisionReward`
  - use: QA checklist + weighted concept score.
  - adaptation: replace generic human/face/image-quality questions with
    architecture-massing questions.
- AesthetiQ:
  - use: filtered pairwise preference alignment after quality gates.
  - code: no official repo found.
- DesignPref:
  - use: designer preference is subjective; local reviewer calibration matters.
  - code: no official repo found.

## Code Map

- `ARR/backend/design/maas/preference/concept_schema.py`
  - preference evidence schema and score aggregation.
- `ARR/backend/design/maas/preference/vlm_scorer.py`
  - OpenAI VLM scorer using architecture QA.
- `ARR/backend/design/maas/preference/candidate_crops.py`
  - crops contact-sheet cards into per-candidate PNGs before VLM scoring.
- `ARR/backend/design/maas/preference/reference_corpus.py`
  - Hugging Face / ArchDaily API reference metadata, image download, and tag
    matching.
- `ARR/backend/design/maas/preference/pairwise_store.py`
  - professor/user pairwise labels.
- `ARR/backend/design/maas/preference/reranker.py`
  - constrained ranking after hard gates.
- `ARR/backend/design/maas/preference/quality_audit.py`
  - end-to-end check that the top candidates are legal, reference-backed,
    non-stepback-dominated, orderly, and preference-scored.
- `ARR/backend/design/maas/preference/harness.py`
  - CLI harness for the second distillation loop.
- `ARR/backend/design/maas/agents/preference_distiller_agent/`
  - folder-based MAAS agent wrapper.

## Data Folders

- `docs/ai-session-memory/reference-corpus/huggingface/`
  - primary external image corpus metadata.
- `docs/ai-session-memory/reference-corpus/archdaily/`
  - ArchDaily URL seed list, API metadata, seeded metadata, Playwright probe
    status, images, and DB manifest.
- `docs/ai-session-memory/reference-corpus/pairwise/`
  - reviewer pairwise labels.

## Failure Rules

- Do not let VLM override law, parking, or paper-alignment gates.
- Do not present `geometry_proxy_fallback` as real VLM scoring.
- Do not train preference on failed/over-repaired candidates.
- Do not let all top candidates collapse into stepback/stair massing.
- Do not claim full PPD fine-tuning; local adaptation uses public VLM/pairwise
  components only.
- Do not count DB collection as success by itself; success requires the
  preference quality audit and rendered PNG to pass.
- Do not send the full 20-card contact sheet as if it were a single candidate.
  VLM scoring must use per-candidate crops so each score maps to one mass.
- Do not claim permit-final parking approval from the second distillation
  harness. Current parking pass means mass-stage count/formula evidence; permit
  review remains a downstream parking/driveway agent task.
