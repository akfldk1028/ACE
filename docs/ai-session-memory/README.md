# 25_ACE AI Session Memory

Read this folder before touching the legal-design visualization work.

## Read Order

1. `PROJECT_MAP.md` - three connected projects and ownership.
2. `DESIGN_FLOW.md` - actual `/design` data path.
3. `LEGAL_COVERAGE.md` - what is implemented vs missing.
4. `VERIFY.md` - CLI and browser verification steps.
5. `OPENCODE.md` - how OpenCode was used in this session.
6. `REPO_CLEANUP.md` - dirty worktree triage and safe cleanup policy.

## Current Priority

The final user-facing target is `http://127.0.0.1:5173/design`, not `/land`.

The key correctness gate is datum/elevation first:

- `datum_result` must exist.
- `datum_result.elevation_source` must be `ngii_local_dem` for the covered Seoul test cases.
- If datum falls back to `open_meteo`, do not trust sunlight/daylight height envelopes.

## Quick Check

```bash
node cli/design-regulation-check/start-local.mjs
node cli/design-regulation-check/run-all.mjs --base http://127.0.0.1:8000
node cli/design-regulation-check/check-design.mjs
```

Expected: `start-local.mjs` opens the local backend/frontend pair and prints `http://127.0.0.1:5174/design`; all bundled verification gates should PASS.

If the browser/VWorld frontend is unreliable, render API-derived section diagrams:

```bash
node cli/design-regulation-check/render-section.mjs --base http://127.0.0.1:8000
ARR/backend/.venv/bin/python cli/design-regulation-check/render_section.py --base http://127.0.0.1:8000
```

Expected: PASS and visual files under `cli/design-regulation-check/out/sections/` or `cli/design-regulation-check/out/pysections/`.
