# Repository Cleanup

## Current Repo Boundary State - 2026-06-24

Treat this workspace as a multi-repo/mixed-legacy workspace. Do not use
`git add .`, broad deletes, or broad cache cleanup from the root.

Latest MAAS/AG-light work is now recorded in both places that track it:

- ARR `master`: pending commit after `35a8a26`
  - Hardens `/design` AG-light interaction without replacing the existing
    modules: default flow now merges template, PNU context, live AG-light bus
    messages, and direct-agent commands; direct-agent controls and right
    collaboration panel have stable test ids; the toolbar no longer exposes the
    horizontal layout toggle, preserving the project-standard vertical flow.
- ACE root `DK-BB`: pending companion commit after `423c271`
  - Records the same ARR code slice plus latest Playwright evidence
    `docs/playwright/design-route-live-verify/ag-light/ag-light-current-1782280160228.png`
    and updated
    `docs/playwright/design-route-live-verify/ag-light/ag-light-current-result.json`.
- ARR `master`: `35a8a26 Fix AG-light vertical edge routing`
  - Fixes AG-light custom edge overlay to keep the original vertical React Flow
    feel: no cubic `C` curves, direct vertical line when nodes share x, and
    right-angle fallback otherwise.
- ACE root `DK-BB`: `ba79faa Record AG-light vertical edge verification`
  - Records the same ARR edge fix in the root index plus latest Playwright
    evidence.
- ACE root `DK-BB`: `460fcc7 Update AG-light verification evidence`
  - Latest Playwright verifier artifact for `/design` AG-light flow after the
    JSON_MODULES team update.
- ACE root `DK-BB`: `2ab0470 Align MAAS legal design team operators`
  - Updates `JSON_MODULES/teams/041_MAAS_Legal_Design_Team.json` so
    `maas_geometry_agent` can propose deterministic design-section operators
    (`diagonal_connect`, `terrace_link`, `sloped_roof_mass`, etc.) while still
    requiring ARR validator recheck.
- ACE root `DK-BB`: `b4d8ab2 Record ARR MAAS design section grammar snapshot`
  - Records the ARR grammar/operator cleanup pass in the root index.
- ARR `master`: `c153efd Add MAAS design section grammar operators`
  - Adds diagonal/terrace/sloped-roof MAAS grammar operators, interpreter
    support, deterministic morphology variants, API option forwarding, and
    tests.
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
- `ARR/backend/design/maas/grammar/data/maas_sequences.v0.json`
- `ARR/backend/design/maas/grammar/data/maas_terms.v0.json`
- `ARR/backend/design/maas/grammar/legal_interpreter.py`
- `ARR/backend/design/maas/grammar/vocab.py`
- `ARR/backend/design/maas/morphology_operators.py`
- `ARR/backend/design/test_maas_export.py`
- `ARR/backend/design/views.py`
- `JSON_MODULES/teams/041_MAAS_Legal_Design_Team.json`
- `docs/playwright/design-route-live-verify/ag-light/ag-light-current-result.json`
- `docs/playwright/design-route-live-verify/ag-light/ag-light-current-1782277791093.png`

Current repo status summary from this session:

- ACE root `DK-BB` at `ba79faa`: still very dirty from old mixed legacy state
  (`AG/`, `ARR/`, `JSON_MODULES/`, docs/tests, weird tracked Windows-path
  deletions, AUA/korean-law-mcp gitlinks). Current MAAS/AG-light and
  JSON_MODULES 041 work is no longer among the dirty target files.
- ARR `master` at `c153efd`: latest AG-light/MAAS files and the first
  grammar/operator cleanup pass are clean. The repo still has a large
  pre-existing dirty set outside this slice.
- AG `master` at `179fe49`: dirty research/autogen tree. Keep separate from ARR
  legal-design work.
- AUA `main` at `2214165`: dirty, separate project pass.
- korean-law-mcp `main` at `6150e13`: dirty, separate law-MCP pass.
- `AG-frontend`, `AG-light`, and `JSON_MODULES` are currently root-owned paths
  from Git's perspective unless a nested `.git` is explicitly present. Do not
  assume they are independent repos.

Cleanup order from here:

1. AUA and korean-law-mcp: separate project-specific review/commit/push passes.
2. Root weird Windows-path tracked deletions and PPT generator deletions need an
   explicit decision before committing or restoring; do not silently decide.

Verification already passed for the latest MAAS/AG-light slice:

- `cd ARR/frontend && npm run type-check` passed after AG-light interaction
  hardening.
- `cd ARR/backend && .venv/bin/python manage.py test design.test_maas_export -v 1`
  passed 56 tests after AG-light interaction hardening.
- `node docs/playwright/design-route-live-verify/ag-light/verify-current-ag-light.cjs`
  passed again; latest PNG:
  `docs/playwright/design-route-live-verify/ag-light/ag-light-current-1782280160228.png`.
- Extra Playwright DOM interaction check passed:
  `initialPaths=5`, direct-agent target changed
  `law_graph_agent -> parking_agent`, right panel collapsed `true` then
  expanded `false`, final `pathCount=5`, `badCurves=[]`, and paths remained
  vertical/right-angle `L` commands.
- `cd ARR/backend && .venv/bin/python manage.py test design.test_maas_export -v 1`
  passed 56 tests again after the design-section grammar cleanup.
- `cd ARR/backend && .venv/bin/python manage.py test design.test_maas_export`
  passed 56 tests.
- `cd ARR/frontend && npm run type-check` passed.
- `node docs/playwright/design-route-live-verify/ag-light/verify-current-ag-light.cjs`
  passed.
- Latest Playwright PNG:
  `docs/playwright/design-route-live-verify/ag-light/ag-light-current-1782277791093.png`.
- Edge-specific DOM check after frontend restart:
  `pathCount=5`, `badCurves=[]`, paths are vertical/right-angle `L` commands.
  This addresses the user screenshot complaint that agent links looked like
  strange sagging diagonal/curved lines. Keep the default AG-light flow vertical.
- JSON_MODULES review note: 72 files initially appeared modified, but all except
  `041_MAAS_Legal_Design_Team.json` were CRLF/LF-only churn. They were
  normalized back to content-clean state and not committed.
- AG review note: the AG repo still reports a large dirty set. With
  `git -C AG diff --ignore-space-at-eol --stat`, the substantive diff collapses
  to 24 files, all under generated/upstream assets such as
  `autogen_a2a_kit/autogen_source/.../autogenstudio/web/ui/**` and bundled image
  assets. Do not commit these in the legal-design cleanup path. The remaining
  apparent research/autogen changes are EOL churn and need a dedicated AG
  normalization policy before any commit.

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
