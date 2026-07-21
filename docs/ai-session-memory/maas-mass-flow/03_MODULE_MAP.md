# Module Ownership Map

Keep changes in the owning module. Do not grow another monolithic benchmark.

## Geometry language

- AST/DSL/compiler: `ARR/backend/design/maas/geometry_language/`
- Universal form supply: `universal_form_bank.py`
- Base-volume and BOOK lowering contracts: `base_volume_audit.py`,
  `book_lowering_contract.py`, `book_parameter_projection.py`
- Program projection: `program_projection.py`
- Truthful run lifecycle/progress: `run_state.py`
- Compiler/GATE: `compiler.py`, `gate.py`
- Per-MASS passport and Agent context: `execution_passport.py`,
  `execution_evidence.py`, `execution_activation.py`,
  `execution_agent_context.py`
- Exact outcome memory: `outcome_graph.py`
- Bounded run-aware read model: `ARR/backend/design/maas/outcome_graph_slice.py`
- Executed archive/run-level VLM manifest: `executed_archive.py`

## Single MASS deploy execution

- Public orchestration boundary: `ARR/backend/design/maas/single_execution/`
- Stable result contract: `single_execution/contracts.py`
- Compile/GATE/render/passport timing pipeline: `single_execution/pipeline.py`
- Atomic bundle writers: `single_execution/persistence.py`
- CLI: `ARR/backend/design/management/commands/execute_maas_single_mass.py`
- HTTP: `POST /design/maas/single-executions/` plus returned preview/passport/
  manifest URLs in `design/views.py` and `design/urls.py`
- Contract tests: `ARR/backend/design/test_maas_single_execution.py`
- Do not add one-MASS execution back into `portfolio_benchmark.py`. Author,
  critic, law and elevation agents exchange the exact GeometryProgram/hash and
  enrich the same passport instead.

## BOOK portfolio pipeline

- Candidate authoring: `ARR/backend/design/maas/book_language/candidate_generation.py`
- Candidate measurements: `candidate_analysis.py`
- Capacity contract/alternatives: `capacity_contract.py`,
  `capacity_alternatives.py`
- Legal/parking evaluation: `downstream_hard_gate.py`
- Bounded page loop: `portfolio_replenishment.py`
- Set selection and diagnostics: `portfolio_selection.py`,
  `portfolio_constraint_solver.py`
- Quality-diversity memory bound and streaming archive:
  `quality_diversity_archive.py`
- Benchmark orchestration only: `portfolio_benchmark.py`
- VLM lifecycle: `vlm_review.py`, `final_vlm_cycle.py`,
  `vlm_stage_policy.py`, `portfolio_feedback.py`
- ArchDaily query context: `reference_context.py`
- Post-run paid individual MASS audit: `geometry_language/executed_vlm_audit.py`
- Post-run paid board audit command:
  `design/management/commands/audit_maas_portfolio_board.py`
- GeometryProgram MASS -> elevation packet: `geometry_language/elevation_handoff.py`
- Same-origin reference image paths: `preference/reference_paths.py`
- Depth-buffered diagnostic renderer: `preference/mesh_rasterizer.py`, consumed
  by `preference/loop.py`. Keep rendering mechanics out of the benchmark.

## Frontend

- Single graph orchestration: `ARR/frontend/src/design/components/book-language-flow/BookLanguageFlow.tsx`
- Network renderer: `LanguageNetworkCanvas.tsx`
- Actual MASS sidebar: `ExecutedMassEvidence.tsx`
- Runtime API/types: `ARR/frontend/src/design/lib/api-client.ts`,
  `language-system-types.ts`
- Browser verification: `docs/playwright/design-route-live-verify/verify-maas-single-graph.cjs`
- Focused MASS-flow regressions: `ARR/backend/design/test_maas_flow_regressions.py`

## Memory update protocol

After every completed run:

1. Never overwrite historical evidence directories.
2. Update `current-checkpoint.json` atomically with the completed run only.
3. Update `02_CURRENT_STATE.md` with verified facts and explicit gaps.
4. Append one entry to `CHANGELOG.md`.
5. Run JSON validation, backend focused tests, TypeScript and browser verify.
6. Record paid VLM request count and `retrieved` versus `used` separately.
7. Record direct PNG review independently from numeric status.
