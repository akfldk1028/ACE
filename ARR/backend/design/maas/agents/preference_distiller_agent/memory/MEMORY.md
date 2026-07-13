# Preference Distiller Agent Memory

Updated: 2026-07-08

The user/professor asked for a second distillation stage: people prefer some
massing alternatives and reject others, so MAAS should learn from those
preferences instead of relying only on law, parking, and LLM language.

Current decision:

- First target remains generator paper alignment.
- Second distillation is a post-legal, post-parking reranker.
- VLM is useful for structured concept scoring from PNGs, but it cannot be the
  legal authority and cannot hide weak source geometry.
- The agent must expose whether it used real VLM inference or only deterministic
  geometry proxy evidence.
- External image use is allowed for research. Hugging Face architecture datasets
  are the primary reference corpus, and ArchDaily is a precedent corpus.
- The implementation follows VisionReward's QA + weighted score pattern and
  PPD's pairwise preference/profile pattern.

Planned data:

- internal MAAS PNG candidates and JSON evidence,
- professor/student pairwise choices,
- user-provided books/reference boards,
- public precedent metadata where license allows.

Current code:

- `design.maas.preference.vlm_scorer` calls OpenAI VLM for architecture QA.
- `design.maas.preference.reference_corpus` normalizes Hugging Face and
  ArchDaily references.
- `design.maas.preference.harness` runs the second mass distillation loop.
- `design.maas.preference.loop` owns the live MAAS preference loop used by the
  legal variants endpoint:
  - builds temporary candidate preview PNGs;
  - matches the reference corpus;
  - runs top-k VLM scoring in parallel;
  - attaches `preference_distillation` evidence;
  - never decides law, parking, or final permit validity.
- `docs/ai-session-memory/SECOND_MASS_DISTILLATION/` is the canonical memory
  folder for this stage.

2026-07-10 verified boundary:

- Top-40 VLM scoring is real and image-backed:
  `preference_loop.attempted_count=40`,
  `preference_loop.vlm_scored_count=40`.
- Final review preservation is not owned here. It lives in
  `design.maas.selection.preference_guards`.
- Final verified sheet keeps 16/20 VLM-scored candidates and 18/20 direct
  OpenAI LLM candidates while legal and parking mass-stage gates remain hard.
