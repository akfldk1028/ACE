# Review Agent Memory

Created: 2026-07-07

The review layer exists because the user needs a presentation-ready distinction between what is proven, what is prototype evidence, and what remains weak.

Current handoff:

`grammar_critic_agent -> review_agent -> design_orchestrator`

2026-07-10 MAAS final-review responsibility:

- Final 20-card review preservation logic is modularized in
  `design.maas.selection.preference_guards`.
- That module does not create geometry and does not decide legality. It only
  curates already legal/parking-stage candidates after balanced selection.
- Current hard review targets:
  - at least 16/20 `vlm_scored` candidates when VLM is required;
  - at least 18/20 direct OpenAI LLM candidates;
  - no one mass language may dominate;
  - height, family, mass-language, and formal-principle diversity must recover
    after VLM preservation.
- The latest verified PNG/JSON passes both:
  - `verify-maas-20-alt-json.cjs`;
  - `verify-maas-png.py`.
