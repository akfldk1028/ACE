# Repository Cleanup - 2026-05-18

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
