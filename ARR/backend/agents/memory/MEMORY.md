# ARR Global A2A Agents Memory

## 2026-07-07

- Clarified that this folder is required alongside MAAS domain agents.
- Added GitAgent-style root metadata so global infrastructure can be inspected
  with the same folder vocabulary as domain agents.
- Existing runtime files are not moved because Django imports and URL routing
  depend on the current module paths.

## 2026-07-21 - Specialist repositories and shared memory

- `ARR/backend/agents/` is the shared multi-agent control plane and shared
  memory/contract layer.
- `ARR/backend/agents/elevationAgent/` is the structural reference for future
  sibling specialist repositories such as `massAgent`, `planAgent`, and
  `lawAgent`.
- Clone the folder vocabulary, never the existing identity, `.git` history, or
  task-specific memory content. Every specialist initializes its own identity,
  rules, memory, skills, tools, tests, and repository history.
- `ARR/backend/design/maas/` remains the shared massing domain engine. A future
  `massAgent` invokes it through typed contracts rather than copying its code.
- Cross-agent artifacts use `run_id`, `program_hash`, `geometry_hash`, PNU,
  evidence IDs, and explicit evaluated/not-evaluated status.
- Full contract: `ARR/backend/agents/SHARED_AGENT_ARCHITECTURE.md`.

## 2026-07-21 - MASS VLM and elevation handoff

- r188 MASS 01, 07 and 10 now have paid individual VLM evidence bound to the
  actual MASS PNG and exact reference-image hashes. Retrieved-only images stay
  inactive.
- MASS 07 is explicitly flagged `too_fragmented`; all three fail individual
  program fit. No agent may promote them to final-elevation approval.
- Elevation handoff schema: `arr.maas.elevation_handoff.v1`.
- The handoff carries run/PNU/program/geometry identity, GeometryProgram,
  indexed mesh, MASS image hash, VLM evidence and approval state.
- The existing `elevationAgent` nested repository has unrelated dirty user
  changes and placeholder private memory; it was intentionally not overwritten.
- Shared research memory is in `docs/ai-session-memory/maas-aesthetic-texturing/`.
