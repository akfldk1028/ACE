# MAAS MASS Flow Memory

This folder is the canonical, modular handoff for the complete MAAS massing
flow. Read these files in order before changing generation, selection, VLM,
legal/parking logic or the `/design/language` graph.

## Product identity

MAAS is a multi-agent legal-to-competition-design system. Its product path is
not a geometry gallery, UnitBox form study, portfolio benchmark, single-MASS
replay or elevation-image test in isolation.

The complete product path is:

`PNU/site -> law Graph DB + deterministic site/datum rules -> legal envelope +
floor-by-floor capacity alternatives -> parking requirements/strategy -> LLM
Architect -> MassDSL -> Geometry Compiler -> floor/legal/program/parking hard
gates -> bounded VLM Critic -> typed repair/recompile loop -> review_agent ->
Selector -> immutable accepted MASS -> elevationAgent -> multi-view facade
consistency -> competition-design evidence package`.

All stages collaborate through evidence, but their authority remains separate:
law and numeric solvers own compliance calculations; the LLM authors typed
architectural intent; the compiler owns executable geometry; VLM is a critic;
and `elevationAgent` may design only on the frozen MASS.

1. `01_FLOW_CONTRACT.md` — stable causal architecture and truth boundaries.
2. `02_CURRENT_STATE.md` — latest verified runtime result and honest limits.
3. `03_MODULE_MAP.md` — code ownership and where a change belongs.
4. `04_VALIDATION_GAPS.md` — unresolved quality and authority gaps.
5. `current-checkpoint.json` — machine-readable current state.
6. `CHANGELOG.md` — append-only checkpoint history.
7. `06_ELEVATION_HANDOFF.md` — GeometryProgram MASS to elevationAgent boundary.
8. `07_FULL_TEST_CONTRACT.md` — mandatory engineering and MAAS acceptance gates.
9. `08_UNITBOX_MATRIX_AUTHORITY.md` — implemented one-root 4x4 geometry and UI contract.

Primary rule: never turn a retrieved image, BOOK scan, unevaluated VLM stage,
or rejected geometry into active evidence. One selected MASS has one exact
causal path inside one graph.

Non-negotiable geometry rule: every MASS operation is relative to the
evaluated Base Model/current Solid. Resolve dimensions, movement, cuts,
repetition and attachments from its local bounds, axes, face frames and
topology. Never hardcode parcel coordinates, absolute completed-form
dimensions or image-specific vertex recipes in synthesis. Dimensionless
sampling/safety policies are allowed only when they are named, centralized,
replaceable and recorded in the Geometry Program.

Canonical-base decision (2026-07-22): there is only one Base Model authority,
the normalized `1/1 UnitBox`. `1/2`, `3/8`, `1/4`, `1/8` and `1/16` are derived
states, not additional primitives. Affine derivations share a homogeneous 4x4
matrix representation; topology-changing Boolean/cut/modifier/pattern/
composition operators remain recursive because a matrix alone cannot generate
all architectural solids. The graph must show `1/1 -> derivation -> MASS`, not
six competing base authorities.

Current audited frontend: `http://127.0.0.1:5178/design/language`.

Fast deploy/runtime rule: a user-facing request executes one explicit
`GeometryProgram` through `ARR/backend/design/maas/single_execution/`; it must
not enter the 20-MASS portfolio benchmark unless portfolio search was actually
requested. The one-MASS bundle always contains the source AST, four-view PNG
(only after geometry GATE), execution passport/causal graph, manifest and
per-stage latency. `geometry_ready` is separate from full legal/VLM acceptance.

Completion rule: always apply `07_FULL_TEST_CONTRACT.md`. A partial unit test,
backend-only implementation, or screenshot can never close a MAAS task.

Current acceptance contract (r204): every new single MASS must traverse the
hash-bound specialist sequence `design_orchestrator -> maas_geometry_agent ->
law_graph_agent -> parking_agent -> review_agent -> selector`. The immutable
identity is `execution_id + program_hash + geometry_hash + PNU`. Missing law
MCP/Neo4j evidence produces `needs_evidence` while preserving the diagnostic
PNG; it can never produce `accepted`. r204 proved live Neo4j and :8011 law
evidence can pass for the exact MASS/PNU identity. Its precedent-informed MASS
still remains `needs_evidence` because the final paid VLM rejected section and
public-threshold fit and full capacity/parking evidence was not supplied.

That r204 sequence is the post-compile single-execution review sequence, not the
complete generative collaboration. The full design-authoring sequence and its
current implementation gaps are defined in `01_FLOW_CONTRACT.md` and
`04_VALIDATION_GAPS.md`. Do not substitute the shorter review sequence for the
product flow.

Multi-agent folder contract: read `05_MULTI_AGENT_FOLDER_CONTRACT.md` before
creating or moving any specialist agent. `ARR/backend/agents/` is the shared
control-plane/memory parent; `ARR/backend/agents/elevationAgent/` is the
structural reference for independent sibling specialist repositories.
