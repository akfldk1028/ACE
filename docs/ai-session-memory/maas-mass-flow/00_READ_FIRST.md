# MAAS MASS Flow Memory

This folder is the canonical, modular handoff for the complete MAAS massing
flow. Read these files in order before changing generation, selection, VLM,
legal/parking logic or the `/design/language` graph.

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

Current frontend: `http://127.0.0.1:5175/design/language`.

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

Multi-agent folder contract: read `05_MULTI_AGENT_FOLDER_CONTRACT.md` before
creating or moving any specialist agent. `ARR/backend/agents/` is the shared
control-plane/memory parent; `ARR/backend/agents/elevationAgent/` is the
structural reference for independent sibling specialist repositories.
