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

Current frontend: `http://127.0.0.1:5175/design/language`.

Fast deploy/runtime rule: a user-facing request executes one explicit
`GeometryProgram` through `ARR/backend/design/maas/single_execution/`; it must
not enter the 20-MASS portfolio benchmark unless portfolio search was actually
requested. The one-MASS bundle always contains the source AST, four-view PNG
(only after geometry GATE), execution passport/causal graph, manifest and
per-stage latency. `geometry_ready` is separate from full legal/VLM acceptance.

Current completed checkpoint: r196 is an honest `15/20 · FAIL`, not the
finished portfolio. It verifies the streaming MAP-Elites memory fix and has no
new paid VLM judgement. r194 remains the latest paid board audit and also
failed. r195 and r197 are state-only `ResourceGuard` failures with no final
MASS PNG; never relabel them as generated portfolios. The current source also
contains an unbenchmarked topology-aware triangular-profile projection fix.
r182 remains the latest numeric `20/20` baseline; it was not VLM-approved.

Multi-agent folder contract: read `05_MULTI_AGENT_FOLDER_CONTRACT.md` before
creating or moving any specialist agent. `ARR/backend/agents/` is the shared
control-plane/memory parent; `ARR/backend/agents/elevationAgent/` is the
structural reference for independent sibling specialist repositories.
