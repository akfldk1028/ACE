# ACE Workspace Harness

This is the project-level verification contract for the legal-design
multi-agent workspace. It is intentionally split by repo responsibility so a
future session can tell whether a failure is legal/mass generation, agent
contract, React Flow UI, or workspace wiring.

## Principle

- PNG is visual evidence.
- JSON is the machine verdict.
- This file is the human handoff.

Do not treat a nice-looking PNG as a pass unless the matching JSON gate also
passes.

## Repo Responsibilities

### ACE root

Owns workspace orchestration and memory.

- Defines the gate order.
- Records current pass/fail summaries and artifact paths.
- Runs fast gates through `scripts/verify-workspace.mjs`.

### JSON_MODULES

Owns team/workflow source of truth.

Required gate:

- `JSON_MODULES/teams/041_MAAS_Legal_Design_Team.json` must contain the six
  canonical MAAS agents:
  - `law_graph_agent`
  - `parking_agent`
  - `massdsl_agent`
  - `maas_geometry_agent`
  - `grammar_critic_agent`
  - `review_agent`

### ARR

Owns legal envelope, parking evidence, mass generation, API, and `/design`
integration.

Fast mass gate:

```bash
node docs/playwright/design-route-live-verify/render-maas-20-alt.cjs
node docs/playwright/design-route-live-verify/verify-maas-20-alt-json.cjs
```

Current minimum acceptance:

- `count >= 20`
- `legalPass == count`
- `uniqueShapes >= 12`
- `uniqueFamilies >= 10`
- `uniqueSections >= 6`
- `materialized >= 12`

Important limitation: this is a legal-envelope mass diversity gate. Parking is
verified by the separate `arr-parking` gate, which distinguishes mass-stage
count/formula satisfaction from permit-level approval.

ARR parking fast gate:

```bash
node docs/playwright/design-route-live-verify/verify-maas-parking-json.cjs
```

Current minimum acceptance:

- required parking count is computed for every candidate;
- formula evidence exists for every candidate;
- planned/provided count is at least the legal required count;
- exact stall polygons exist for non-mechanical layouts, or mechanical parking
  evidence exists for mechanical layouts;
- all candidates pass the mass-stage parking gate.

ARR agent contract gate:

- `ARR/backend/design/maas/agents/{agent}/agent.py`
- `ARR/backend/design/maas/agents/{agent}/card.py`
- `ARR/backend/design/maas/agents/{agent}/contract.py`

must exist for:

- `law_graph_agent`
- `parking_agent`
- `massdsl_agent`
- `maas_geometry_agent`
- `grammar_critic_agent`
- `review_agent`

### AG

Owns reusable agent/A2A research and backend agent patterns.

Current root gate only checks that AG agent source folders exist. The next real
AG gate should execute a small fixture conversation and verify message handoff
between law, parking, MassDSL, geometry, critic, and review roles.

### AG-frontend

Owns the full React Flow-style collaboration UI patterns.

Current root gate checks that the existing AG-frontend e2e flow specs and
playground flow source files exist. The next real AG-frontend gate should run
the relevant Playwright spec and assert draggable/selectable nodes, edge
layout, and agent-specific direct-command routing.

### ARR Frontend AG-light

Owns the integrated `/design` right-side collaboration panel.

Fast latest-result gate checks:

- `hasReactFlow`
- `reactFlowNodes >= 6`
- `overlayEdges >= 5`
- PNU transfer text includes law, parking, MassDSL, geometry, grammar, and
  review handoff labels.

Live Playwright gate:

```bash
FRONTEND_URL=http://localhost:5174/design \
node docs/playwright/design-route-live-verify/ag-light/verify-current-ag-light.cjs
```

Use live gate after frontend edits. Use latest-result gate for quick workspace
sanity.

## Gate Order

Fast workspace gate:

```bash
node scripts/verify-workspace.mjs --quick
```

Expected order:

1. JSON_MODULES team schema.
2. ARR MAAS agent contract files.
3. ARR latest mass JSON verdict.
4. ARR latest parking JSON verdict.
5. ARR AG-light latest UI verdict.
6. AG / AG-frontend presence gates.

Live ARR mass gate:

```bash
node scripts/verify-workspace.mjs --gate arr-mass --render
```

This requires the ARR backend at `http://127.0.0.1:18000`.

Full workspace direction:

- Fast gates should be cheap and run during every design/mass iteration.
- Live Playwright and Django benchmark gates are final/periodic checks.
- `benchmark_maas_algorithms` is useful for research/algorithm evidence but too
  slow for the inner edit loop.

## Latest Known Fast Result

Date: 2026-06-30

PNU: `1168011800104170004`

Artifacts:

- `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
- `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`
- `docs/playwright/design-route-live-verify/ag-light/ag-light-current-result.json`

ARR mass JSON summary:

- `count=20`
- `legalPass=20`
- `uniqueShapes=15`
- `uniqueFamilies=14`
- `uniqueSections=10`
- `materialized=17`
- `parkingCountSatisfied=20`
- `parkingMassStagePass=20`
- `parkingPermitPass=0`

ARR parking JSON summary:

- `requiredComputed=20`
- `formulaEvidence=20`
- `countSatisfied=20`
- `exactOrMechanicalEvidence=20`
- `massStageParkingPass=20`
- `permitParkingPass=0`
- `needs_mechanical_parking_review=13`
- `needs_drive_connectivity_review=7`

ARR AG-light latest-result summary:

- `hasReactFlow=true`
- `reactFlowNodes=8`
- `overlayEdges=7`
- transfer text includes PNU and the six-stage handoff.
