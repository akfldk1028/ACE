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

## Current Dirty Buckets

After the ignore cleanup, untracked files are still mostly real project material, not disposable cache:

- `ARR/`: large untracked application tree and many modified files. This is the main `/design` source of truth. Do not bulk ignore it.
- `AG-light/`: real lightweight Worker/FastAPI project source. `node_modules/` and `vectors.ndjson` are ignored; about 88 source/data/docs files remain untracked and should be reviewed as a project import.
- `AG/AG-Research/`: many tracked modified research/result files. Much of the apparent churn is line-ending/result-data noise. Do not stage broadly with legal app work.
- `JSON_MODULES/`: modified multi-agent JSON/module files. Treat as a separate agent-config cleanup unit.
- `docs/`: user reference images and legal screenshots live here. Do not ignore/delete broadly.
- `tests/`, `cli/`, top-level handoff/overleaf files: small mixed artifacts; inspect one-by-one.

## Recommended Cleanup Order

1. Keep ignore-only changes separate from source changes.
2. Import/commit `AG-light/` as its own unit only after checking it does not include secrets or generated artifacts.
3. Split `ARR/` into backend, frontend, and docs/test commits instead of staging the whole tree.
4. Leave `AG/AG-Research` and `JSON_MODULES` for separate research/agent-config commits because they are not part of the `/design` legal rendering change.
5. Before any push, run `git status --short`, `git diff --cached --stat`, and verify no `node_modules`, `.env`, generated vectors, or CLI output directories are staged.

## Current Legal QA State To Preserve

- `/design` is the final target, not `/land`.
- ARR backend computes `/design/site-boundary/` and `/design/auto-constraints/`.
- AG-light is useful as a lightweight legal-agent project, but it does not yet have ARR-equivalent datum computation.
- VWorld default view should stay sparse and Flexity-style: parcel, road/neighbor context, compact datum markers, and clean legal surfaces/lines rather than dense debug fences.
- Datum correctness comes first. If `datum_result.elevation_source` is not `ngii_local_dem` for covered Seoul cases, do not trust sunlight/daylight envelopes.
