# Repository Cleanup

## Current Repo Boundary State - 2026-06-24

Treat this workspace as a multi-repo/mixed-legacy workspace. Do not use
`git add .`, broad deletes, or broad cache cleanup from the root.

Latest MAAS/AG-light work is now recorded in both places that track it:

- ACE root `DK-BB`: `a7932c1 Record ARR MAAS design quality snapshot`
  - This records the ARR MAAS design-quality/research-backend/frontend flow
    files in the root index because the root repo still tracks ARR files.
- ARR `master`: `dc0e6f1 Add MAAS design quality and AG-light flow evidence`
  - This is the real ARR repo commit for the same implementation.
- Root docs/evidence commit before that:
  `f34f5b2 Document MAAS AG-light verification state`.

Verified latest files are clean in both root and ARR after the snapshot:

- `ARR/backend/design/maas/design_quality.py`
- `ARR/backend/design/maas/legal_mesh_optimizer.py`
- `ARR/backend/design/maas/research_backends/`
- `ARR/backend/requirements.txt`
- `ARR/frontend/src/design/DesignPage.tsx`
- `ARR/frontend/src/design/components/DefaultAgentFlowPanel.tsx`
- `ARR/frontend/src/design/components/InteractiveDesignPanel.tsx`
- `ARR/frontend/src/design/components/ag-light-flow/`

Current repo status summary from this session:

- ACE root `DK-BB` at `a7932c1`: still very dirty from old mixed legacy state
  (`AG/`, `ARR/`, `JSON_MODULES/`, docs/tests, weird tracked Windows-path
  deletions, AUA/korean-law-mcp gitlinks). The current MAAS/AG-light work is
  no longer among the dirty target files.
- ARR `master` at `dc0e6f1`: latest AG-light/MAAS files are clean. The repo
  still has a large pre-existing dirty set, including older MAAS grammar/operator
  files such as `backend/design/maas/grammar/*` and
  `backend/design/maas/morphology_operators.py`. Review and commit those as a
  separate ARR pass only.
- AG `master` at `179fe49`: dirty research/autogen tree. Keep separate from ARR
  legal-design work.
- AUA `main` at `2214165`: dirty, separate project pass.
- korean-law-mcp `main` at `6150e13`: dirty, separate law-MCP pass.
- `AG-frontend`, `AG-light`, and `JSON_MODULES` are currently root-owned paths
  from Git's perspective unless a nested `.git` is explicitly present. Do not
  assume they are independent repos.

Cleanup order from here:

1. ARR old MAAS grammar/operator changes: inspect intent, run ARR backend tests,
   commit only if they are coherent with the MAAS sequence/vocab direction.
2. JSON_MODULES agent/team configs: separate root commit after validating that
   AG-light flow still maps agents/teams correctly.
3. AG research/autogen generated artifacts: separate AG pass; avoid committing
   generated `autogenstudio/web/ui/**` unless intentionally preserving a build.
4. AUA and korean-law-mcp: separate project-specific review/commit/push passes.
5. Root weird Windows-path tracked deletions and PPT generator deletions need an
   explicit decision before committing or restoring; do not silently decide.

Verification already passed for the latest MAAS/AG-light slice:

- `cd ARR/backend && .venv/bin/python manage.py test design.test_maas_export`
  passed 56 tests.
- `cd ARR/frontend && npm run type-check` passed.
- `node docs/playwright/design-route-live-verify/ag-light/verify-current-ag-light.cjs`
  passed.
- Latest Playwright PNG:
  `docs/playwright/design-route-live-verify/ag-light/ag-light-current-1782262074594.png`.

## Repository Cleanup - 2026-05-18

The workspace started with a very large pre-existing dirty/untracked state. Do not run broad cleanup or revert commands without user approval.

## Commits Made

- `d6d7942 Add design regulation QA and VWorld capture gate`
  - Scoped to ARR `/design` legal QA, VWorld capture CLI, and related memory/test tooling.
- `6c8d65e Ignore local generated artifacts`
  - Added ignore rules for local/generated artifacts:
    - dependency/build/cache dirs across nested projects
    - `.code-review-graph/`
    - `cli/design-regulation-check/out/`
    - `AG-light/vectors.ndjson`
    - local scratch files such as `clone/`, `Data25_ACEtmp_resp.json`, test stdout/stderr logs, and `tmp_plateau_check.py`
- `283d833 Document design QA handoff and cleanup state`
  - Added this memory folder to the repo so future sessions have a stable handoff path.
- `834517b Add AG-light legal agent project`
  - Added AG-light source/data/docs as a real connected project.
  - Confirmed ignored exclusions: `.env`, `.claude/`, `node_modules/`, logs, and `vectors.ndjson`.
- `e779e14 Preserve ARR datum and sunlight basis fixes`
  - Committed the seven substantive ARR tracked changes after targeted backend tests passed.
  - Test command: `.venv/bin/python manage.py test land.tests.DatumElevationApiTest land.tests.DatumCalculatorTest land.tests.DatumCasesTest land.tests.SetbackGeometryDatumTest`
  - Result: 34 tests passed.

## Current Dirty Buckets

After the ignore cleanup, untracked files are still mostly real project material, not disposable cache:

- `ARR/`: large untracked application tree remains. This is the main `/design` source of truth. Do not bulk ignore it. Current tracked ARR source changes with actual content were committed in `e779e14`; remaining tracked `M` status is EOL-only by `git diff --ignore-space-at-eol --numstat`.
- `AG-light/`: committed in `834517b`. Future dirty AG-light should be treated as normal source changes, with generated vectors and dependencies ignored.
- `AG/AG-Research/`: many tracked modified research/result files. Current tracked changes appear to be mostly EOL/result-data churn. Do not stage broadly with legal app work.
- `JSON_MODULES/`: modified multi-agent JSON/module files. Treat as a separate agent-config cleanup unit.
- `docs/`: user reference images and legal screenshots live here. Do not ignore/delete broadly.
- `tests/`, `cli/`, top-level handoff/overleaf files: small mixed artifacts; inspect one-by-one.

## Recommended Cleanup Order

1. Keep ignore-only changes separate from source changes.
2. Import/commit `AG-light/` as its own unit only after checking it does not include secrets or generated artifacts.
3. Split remaining untracked `ARR/` into backend, frontend, and docs/test commits instead of staging the whole tree.
4. Leave `AG/AG-Research` and `JSON_MODULES` for separate research/agent-config commits because they are not part of the `/design` legal rendering change.
5. Before any push, run `git status --short`, `git diff --cached --stat`, and verify no `node_modules`, `.env`, generated vectors, or CLI output directories are staged.

## Current Legal QA State To Preserve

- `/design` is the final target, not `/land`.
- ARR backend computes `/design/site-boundary/` and `/design/auto-constraints/`.
- AG-light is useful as a lightweight legal-agent project, but it does not yet have ARR-equivalent datum computation.
- VWorld default view should stay sparse and Flexity-style: parcel, road/neighbor context, compact datum markers, and clean legal surfaces/lines rather than dense debug fences.
- Datum correctness comes first. If `datum_result.elevation_source` is not `ngii_local_dem` for covered Seoul cases, do not trust sunlight/daylight envelopes.
