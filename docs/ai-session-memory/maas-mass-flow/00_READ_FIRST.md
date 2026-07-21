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

Current runtime checkpoint: r194 is the newest run from the current production
source and is an honest `15/20 · FAIL`, not the finished portfolio. Its
downstream site/legal/parking preflight passes, its run-local causal graph and
single-graph frontend replay work, and its one paid post-render portfolio VLM
audit also fails. The remaining bottleneck is viable, materially distinct
hard-pass geometry supply, especially triangular/non-quadrilateral plans,
courtyard/split/cross/terrace relations and less repetitive roof archetypes.
r182 remains the latest numeric `20/20` baseline; it was not VLM-approved.

Multi-agent folder contract: read `05_MULTI_AGENT_FOLDER_CONTRACT.md` before
creating or moving any specialist agent. `ARR/backend/agents/` is the shared
control-plane/memory parent; `ARR/backend/agents/elevationAgent/` is the
structural reference for independent sibling specialist repositories.
