# MAAS VLM Preference Source Audit

Updated: 2026-07-08

Purpose: keep the second-stage preference direction grounded in actual paper
text and available code. VLM is the right direction only as a structured critic
and feature extractor, not as a legal or final design authority.

## Cloned Sources

### PPD: Personalized Preference Fine-tuning of Diffusion Models

- Paper: https://arxiv.org/abs/2501.06655
- CVPR paper: https://openaccess.thecvf.com/content/CVPR2025/papers/Dang_Personalized_Preference_Fine-tuning_of_Diffusion_Models_CVPR_2025_paper.pdf
- Official code: https://github.com/Asap7772/Personalized-Text-To-Image-Diffusion
- Local clone: `clone/Personalized-Text-To-Image-Diffusion`
- Local commit: `fe3835f`
- License: Apache-2.0
- Important limitation: the repository explicitly states that it only includes
  Stage 1, the VLM component. The diffusion fine-tuning Stage 2 is not
  open-sourced.

What MAAS should borrow:

- Few-shot pairwise preference examples.
- VLM-generated preference profile/user embedding idea.
- Evaluation by win-rate between alternatives.

What MAAS should not claim:

- Do not claim full PPD diffusion fine-tuning is implemented.
- Do not claim a trained architecture preference model until MAAS pairwise
  labels exist.

### VisionReward

- Paper: https://arxiv.org/abs/2412.21059
- AAAI page: https://ojs.aaai.org/index.php/AAAI/article/view/38107
- Official code: https://github.com/zai-org/VisionReward
- Local clone: `clone/VisionReward`
- Local commit: `511960d`
- License: Apache-2.0

What MAAS should borrow:

- Fine-grained, multi-dimensional visual reward structure.
- QA checklist style:
  - `VisionReward_Image/VisionReward_image_qa.txt`
  - `VisionReward_Image/weight.json`
- Score = VLM yes/no or scalar answers over interpretable questions, then
  weighted sum.

What MAAS must change:

- Replace generic image questions such as human body/face/hand with
  architecture-massing questions:
  - clear dominant mass gesture,
  - readable main/support hierarchy,
  - non-stair silhouette,
  - void/courtyard/publicness quality,
  - precedent resonance,
  - repair integrity,
  - low visual clutter.

### AesthetiQ

- Paper: https://arxiv.org/abs/2503.00591
- CVPR paper: https://openaccess.thecvf.com/content/CVPR2025/papers/Patnaik_AesthetiQ_Enhancing_Graphic_Layout_Design_via_Aesthetic-Aware_Preference_Alignment_of_CVPR_2025_paper.pdf
- Project page: https://mdsrlab.github.io/2025/03/01/AesthetiQ-CVPR.html
- Local clone: none found on 2026-07-08.
- Reason: no official public code repository was found during search.

What MAAS should borrow:

- Generate multiple candidates.
- Filter low-quality candidates with hard heuristics before preference learning.
- Use a VLM/MLLM judge for pairwise aesthetic preference only after quality
  filtering.

### DesignPref

- Paper: https://arxiv.org/abs/2511.20513
- HTML: https://arxiv.org/html/2511.20513v1
- Local clone: none found on 2026-07-08.
- Reason: no official public code repository was found during search.

What MAAS should borrow:

- Professional designers disagree; aggregate majority preference is not enough.
- Store local professor/student preference identity.
- Prefer personalized calibration over one universal beauty score.

## MAAS Implementation Direction

The correct 2nd distillation design is:

```text
legal/parking/source-geometry hard-gated MAAS candidates
-> canonical PNG cards + candidate JSON evidence
-> VLM architectural QA checklist
-> concept score vector
-> professor/student pairwise labels
-> lightweight personalized reranker
-> final legal candidate ordering
```

Do not invert the order. VLM and preference reranking operate only after hard
legal and parking gates.

## Immediate Code Translation

- Use VisionReward as the direct code pattern:
  - create `architecture_massing_qa.v1.json`,
  - create `architecture_massing_weights.v1.json`,
  - implement a scorer that can call a VLM or run geometry proxy mode.
- Use PPD as the preference personalization pattern:
  - store `preferred_candidate_id`,
  - store `rejected_candidate_id`,
  - store `reviewer_id` such as `professor`, `student`, or `user`,
  - aggregate into a reviewer-specific preference profile.
- Keep AesthetiQ as the filtered-pairwise-training pattern:
  - do not train on candidates that fail law, parking, repair integrity, or
    basic orderliness.

## Implemented Local Mapping

- `design.maas.preference.vlm_scorer`
  - follows PPD's OpenAI multimodal message pattern and VisionReward's
    architecture QA pattern.
- `design.maas.preference.reference_corpus`
  - stores Hugging Face and ArchDaily references in one schema.
- `design.maas.preference.pairwise_store`
  - stores PPD-style preferred/rejected labels.
- `design.maas.preference.reranker`
  - follows AesthetiQ's "preference after filtering" principle by reranking
    only hard-gated candidates.
- `design.maas.preference.harness`
  - combines paper/code provenance, references, VLM/proxy score, pairwise wins,
    and constrained reranking.
