# Design Orchestrator Memory

Created: 2026-07-07

MAAS currently spans three active project layers:

- `ARR`: backend legal/massing execution and frontend AG-light flow mapping.
- `JSON_MODULES`: declarative AG/AutoGen team definition.
- `AG-light`: collaboration UI, bus, shared memory, and MCP tools.

The orchestrator must keep these layers aligned.

2026-07-10 MAAS module boundary after cleanup:

- `design.maas.legal_mesh_optimizer`
  - remains the endpoint orchestrator and legal geometry compiler;
  - should not accumulate new VLM scorer or final guard internals.
- `design.maas.llm_proposals`
  - owns OpenAI MassDSL population generation;
  - supports `batch_workers` and `cache_path` so research loops can reuse a
    120-candidate population instead of blocking every verification run.
- `design.maas.preference.loop`
  - owns second-stage image/reference/VLM preference scoring.
- `design.maas.selection.preference_guards`
  - owns final 20-card VLM/direct-LLM/diversity preservation after balanced
    selection.
- Current verified output:
  - LLM cache hit;
  - VLM top-40 scored 40/40;
  - final VLM-scored 16/20;
  - final direct LLM 18/20;
  - JSON and PNG verifiers pass.

Next research-grade gap:

- Implement critic-to-geometry mutation as a real agent loop, not only final
  selection repair.
- Implement EvoMass-style island evolution/performance feedback instead of
  only quota-balanced selection.
